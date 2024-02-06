import re

from django.core.validators import MinValueValidator
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from users.models import Follow, User
from .utils import subscribed_check


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
        return subscribed_check(request, instance)


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
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('amount', 'name', 'measurement_unit', 'id')


class RecipeListSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    image = Base64ImageField(required=True)

    def get_is_favorited(self, instance):
        request = self.context.get('request')
        if not request:
            return False
        return (request.user.is_authenticated and Favorite.objects.filter(
            user=request.user, recipe=instance
        ).exists())

    def get_is_in_shopping_cart(self, instance):
        request = self.context.get('request')
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
            'is_in_shopping_cart',
            'is_favorited',
        )


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        write_only=True,
        min_value=1
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    cooking_time = serializers.IntegerField(
        validators=(MinValueValidator(
            limit_value=1,
            message='Время приготовления не может занимать меньше минуты'
        ),)
    )

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

    def recipe_ingredient_create(self, ingredients_data, recipe):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    ingredient_id=ingredient['id'],
                    amount=ingredient['amount'],
                    recipe=recipe
                ) for ingredient in ingredients_data
            ]
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.recipe_ingredient_create(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.ingredients.clear()
        self.recipe_ingredient_create(ingredients_data, instance)
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
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )


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


class FollowSerializer(serializers.ModelSerializer):
    recipes = RecipeShortSerializer(many=True)
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

    def get_recipes_count(self, instance):
        return Recipe.objects.filter(author__id=instance.id).count()

    def get_is_subscribed(self, instance):
        request = self.context.get('request')
        return subscribed_check(request, instance)


class FollowCreateSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='id',
        queryset=User.objects.all()
    )
    author = serializers.SlugRelatedField(
        slug_field='id', queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Подписаться на себя невозможно.'
            )
        if Follow.objects.filter(
                user=user, author=author
        ).exists():
            raise serializers.ValidationError(
                'Повторная подписка на автора невозможна.'
            )
        return data

    def create(self, validated_data):
        return Follow.objects.create(**validated_data)


class FavoriteCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if self.context['request'].method == 'POST':
            if Favorite.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Повторное добавление избранное невозможно.'
                )
        elif self.context['request'].method == 'DELETE':
            if not Favorite.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в избранных.'
                )
        return data

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)


class ShoppingListCreateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')

    def validate(self, data):
        user = self.context['request'].user
        recipe = data['recipe']
        if self.context['request'].method == 'POST':
            if ShoppingList.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Повторное добавление в список покупок невозможно.'
                )
        elif self.context['request'].method == 'DELETE':
            if not ShoppingList.objects.filter(
                    user=user, recipe=recipe
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в списке покупок.'
                )
        return data

    def create(self, validated_data):
        return ShoppingList.objects.create(**validated_data)
