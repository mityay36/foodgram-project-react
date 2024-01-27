from django.contrib.auth import get_user_model
from django_filters import rest_framework

from recipes.models import Ingredient, Recipe

User = get_user_model()


class RecipeFilter(rest_framework.FilterSet):
    is_favorite = rest_framework.BooleanFilter(
        method="is_favorite_method",
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
    tags = rest_framework.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='Тэги'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorite',
            'is_in_shopping_cart'
        )

    def is_favorite_method(self, queryset, name, value):
        if value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset.exclude(
            favorites__user=self.request.user
        )

    def in_shopping_cart_method(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset


class IngredientFilter(rest_framework.FilterSet):

    name = rest_framework.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
