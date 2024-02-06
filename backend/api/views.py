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
from .serializers import (CustomUserSerializer, FavoriteCreateSerializer,
                          FollowCreateSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeListSerializer, ShoppingListCreateSerializer,
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
            serializer = FollowCreateSerializer(
                data={
                    'user': request.user.id,
                    'author': id
                },
                context={'request': request}
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save(author=author, user=self.request.user)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
        subscription = Follow.objects.filter(user=request.user, author=author)
        if subscription.exists():
            subscription.delete()
            return Response(
                {'message': 'Вы отписались от автора.'},
                status=status.HTTP_204_NO_CONTENT
            )
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

    def add_recipe(self, pk, request, custom_serializer):
        serializer = custom_serializer(
            data={'recipe': pk},
            context={'request': request}
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save(user=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe(self, pk, request, custom_serializer, model):
        serializer = custom_serializer(data={'recipe': pk},
                                       context={'request': request})
        serializer.is_valid(raise_exception=True)
        model_obj = model.objects.get(
            user=request.user,
            recipe=serializer.validated_data['recipe'])
        model_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(pk, request, FavoriteCreateSerializer)
        return self.delete_recipe(
            pk, request, FavoriteCreateSerializer, Favorite
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(pk, request, ShoppingListCreateSerializer)
        return self.delete_recipe(
            pk, request, ShoppingListCreateSerializer, ShoppingList
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_list__user=self.request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').annotate(
            amount_of_item=Sum('amount'))
        purchased = [
            "Список покупок:",
        ]
        for item in ingredients:
            purchased.append(
                f"{item['ingredient__name']}: {item['amount_of_item']}, "
                f"{item['ingredient__measurement_unit']}"
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
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
