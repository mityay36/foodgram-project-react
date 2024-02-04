from django_filters import rest_framework
from django.contrib.auth import get_user_model
from recipes.models import Ingredient, Recipe, Tag

User = get_user_model()


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(rest_framework.FilterSet):
    is_favorited = rest_framework.BooleanFilter(
        method="is_favorited_method",
        label='Избранные рецепты'
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method="in_shopping_cart_method",
        label='Рецепты в корзине'
    )
    author = rest_framework.ModelChoiceFilter(
        field_name='author',
        label='Автор',
        queryset=User.objects.all()
    )
    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Тэги'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def is_favorited_method(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset.exclude(
            favorites__user=self.request.user
        )

    def in_shopping_cart_method(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
