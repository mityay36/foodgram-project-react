from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    is_favorited = filters.BooleanFilter(
        method="is_favorited_method",
        label='Избранные рецепты'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method="in_shopping_cart_method",
        label='Рецепты в корзине'
    )
    tags = filters.ModelMultipleChoiceFilter(
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
            return queryset.filter(favorites__user=self.request.user)
        return queryset.exclude(
            favorites__user=self.request.user
        )

    def in_shopping_cart_method(self, queryset, name, value):
        if value:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset
