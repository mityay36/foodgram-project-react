from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingList, Tag)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .serializers import (CustomUserSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeListSerializer, RecipeShortSerializer,
                          TagSerializer)


class CustomPaginator(pagination.PageNumberPagination):
    page_size_query_param = 'limit'


class UserCustomViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator
    serializer_class = CustomUserSerializer

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        following_users = User.objects.filter(
            following__user=self.request.user
        )
        paginated_queryset = self.paginate_queryset(following_users)
        serializer = FollowSerializer(
            paginated_queryset,
            context={'request': request},
            many=True
        )
        if paginated_queryset is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        serializer_class=FollowSerializer
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        if request.method == 'POST':
            is_subscribed = Follow.objects.filter(
                user=request.user, author=author
            )
            if is_subscribed.exists():
                return Response(
                    {'message': 'Вы уже подписались на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                Follow.objects.create(
                    user=request.user,
                    author=author
                )
                serializer = FollowSerializer(
                    author,
                    context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        subscription = Follow.objects.filter(user=request.user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(
                {'message': 'Вы отписались от автора.'},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {'message': 'Вы не были подписаны на автора'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = CustomPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    def add_recipe(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe_in_model = model.objects.filter(user=user, recipe=recipe)
        if recipe_in_model.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            model.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        recipe_in_model = model.objects.filter(user=user, recipe=recipe)
        if recipe_in_model.exists():
            recipe_in_model.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(Favorite, request.user, pk)
        else:
            return self.delete_recipe(Favorite, request.user, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(ShoppingList, request.user, pk)
        else:
            return self.delete_recipe(ShoppingList, request.user, pk)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingList.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values("ingredient")
            .annotate(amount=Sum("amount"))
        )

        purchased = [
            "Список покупок:",
        ]
        for item in buy:
            ingredient = Ingredient.objects.get(pk=item["ingredient"])
            amount = item["amount"]
            purchased.append(
                f"{ingredient.name}: {amount}, "
                f"{ingredient.measurement_unit}"
            )
        purchased_file = "\n".join(purchased)

        response = HttpResponse(purchased_file, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )
        return response


class TagViwSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
