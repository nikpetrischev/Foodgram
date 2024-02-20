from enum import Enum
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as drf_filters

from rest_framework import filters, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
)

from .serializers import (
    RecipeSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
    IngredientsReadSerializer
)
from users.serializers import UserSerializer, FavouritesSerializer
from .utils import RecipeFilter
from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    UserRecipe,
)

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientsReadSerializer
    queryset = Ingredient.objects.order_by('id')
    filter_backends = [filters.SearchFilter]
    search_field = ['name']
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.order_by('id')
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method in ['GET']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(self, request, *args, **kwargs):
        if request.method in ['POST']:
            recipe = get_object_or_404(
                Recipe,
                pk=kwargs.get('pk'),
            )
            if UserRecipe.objects.filter(
                    user=request.user.id,
                    recipe=recipe.id,
            ).exists():
                return Response(
                    data={'errors': 'Рецепт уже в избранном'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            serializer = FavouritesSerializer(
                data={
                    'recipe': recipe.id,
                    'user': request.user.id,
                },
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    data={
                        'id': recipe.id,
                        'name': f'{recipe.name}',
                        'image': f'{recipe.image}',
                        'cooking_time': recipe.cooking_time,
                    },
                    status=HTTPStatus.CREATED,
                )
        elif request.method in ['DELETE']:
            favourite = get_object_or_404(
                UserRecipe,
                recipe=kwargs.get('pk'),
                user=request.user.id,
            )
            favourite.delete()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(status=HTTPStatus.BAD_REQUEST)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
