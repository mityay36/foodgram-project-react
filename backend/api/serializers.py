import re

from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from users.models import Follow, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name'
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'name', 'measurement_unit', 'id')


class RecipeListSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    in_shopping_cart = serializers.SerializerMethodField()
    author = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField(required=True)

    def get_ingredients(self, obj):
        return RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=obj).all(),
            many=True
        ).data

    def get_is_favorited(self, instance):
        request = self.context.get('request')
        if not request:
            return False
        return (request.user.is_authenticated and Favorite.objects.filter(
            user=request.user, recipe=instance
        ).exists())

    def get_in_shopping_cart(self, instance):
        request = self.context.get('request')
        if not request:
            return False
        return (request.user.is_authenticated and ShoppingList.objects.filter(
            user=request.user, recipe=instance
        ).exists())

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
            'in_shopping_cart',
            'is_favorited',
        )


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    class Meta:
        model = RecipeIngredient
        fields = ('recipe', 'id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)

    def validate_ingredients(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                'Требуется не менее одного ингредиента.'
            )

        existing_ingredients = []
        for ingredient in value:
            if ingredient in existing_ingredients:
                raise serializers.ValidationError(
                    'Ингредиент не может повторяться.'
                )
            existing_ingredients.append(ingredient)
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        create_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(
            create_ingredients
        )
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()

        create_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(
            create_ingredients
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        self.fields.pop('ingredients')
        representation = super().to_representation(instance)
        representation['ingredients'] = RecipeIngredientSerializer(
            RecipeIngredient.objects.filter(recipe=instance).all(), many=True
        ).data
        return representation

    class Meta:
        model = Recipe
        fields = ('name', 'ingredients', 'text')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'cooking_time',
            'image'
        )


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'first_name',
            'last_name',
            'password'
        )

    def validate_username(self, value):
        if not re.match(r'^[\w.@+-]+\Z`', value):
            raise serializers.ValidationError(
                'Поле username содержит недопустимые символы.'
            )
        return value


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'password'
        )

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
        if not request:
            return False
        return (request.user.is_authenticated and Follow.objects.filter(
            user=request.user, author=instance
        ).exists())


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)


class FollowSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, instance):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        if recipes_limit:
            recipes = instance.recipes.all()[:int(recipes_limit)]
        else:
            recipes = instance.recipes.all()
        return RecipeShortSerializer(
            recipes, many=True
        ).data()

    def get_recipes_count(self, instance):
        return Recipe.objects.filter(author__id=instance.id).count()

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
        return (Follow.objects.filter(
            user=request.user, author=instance
        ).exists() and request.user.is_authenticated)

    def validate(self, data):
        request = self.context.get('request')
        if Follow.objects.filter(
                user=request.user, author=data['id']
        ).exists():
            raise serializers.ValidationError(
                'Повторная подписка на автора невозможна.'
            )
        if request.user == get_object_or_404(Follow, pk=self.context['id']):
            raise serializers.ValidationError(
                'Подписаться на себя невозможно.'
            )
        return data


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        if Follow.objects.filter(
            user=self.context['request'].user, recipe_id=data['id']
        ).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в избранном.'
            )


class ShoppingCartSerializer(serializers.ModelSerializer):
    def validate(self, data):
        request = self.context.get('request')
        if ShoppingList.objects.filter(
            user=request.user,
            recipe=data['id']
        ).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в списке покупок'
            )
        return data
