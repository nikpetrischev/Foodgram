# Standard Library
from http import HTTPStatus
from typing import Optional

# Django Library
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django_filters import rest_framework as drf_filters

# DRF Library
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

# Local Imports
from .filters import NameSearchFilter, RecipeFilter
from .mixins import PatchNotPutModelMixin
from .permissions import RecipePermission
from .renderers import ShoppingCartRenderer
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortenedRecipeSerializer,
    TagSerializer,
)
from .utils import (
    check_field_in_user_recipe,
    get_recipe_or_error,
    uncheck_field_in_user_recipe,
)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


class IngredientViewSet(ReadOnlyModelViewSet):
    """
    A viewset for viewing ingredients.

    This viewset provides read-only access to the Ingredient model.
    """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.order_by('id')
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_class = NameSearchFilter
    pagination_class = None
    permission_classes = [permissions.AllowAny]


class RecipeViewSet(
    GenericViewSet,
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    PatchNotPutModelMixin,
):
    """
    A viewset for managing recipes.

    This viewset provides CRUD operations for the Recipe model, including
    custom actions for favoriting and adding recipes to the shopping cart.
    """
    queryset = Recipe.objects.order_by('id')
    filter_backends = [drf_filters.DjangoFilterBackend]
    filterset_class = RecipeFilter
    permission_classes = [RecipePermission]

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the request method.

        Returns:
            The serializer class to use for the request.
        """
        if self.request.method in ['GET']:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        """
        Sets the author of the recipe to the current user upon creation.

        Args:
            serializer: The serializer for the recipe.
        """
        serializer.save(author=self.request.user)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite(
            self,
            request: Request,
            pk: int = None,
    ) -> Response:
        """
        Adds a recipe to the user's favorites.

        Args:
            request: The request object.
            pk: The primary key of the recipe to favorite.

        Returns:
            A response indicating success or failure.
        """
        recipe, error = get_recipe_or_error(pk)
        # type: Optional[Recipe], Optional[Response]
        if error:
            return error

        errors: Optional[Response] = check_field_in_user_recipe(
            request.user,
            recipe,
            is_favorited=True,
        )
        if errors:
            return errors

        return Response(
            ShortenedRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )

    @favorite.mapping.delete
    def favorite_delete(
            self,
            request: Request,
            pk: int = None,
    ) -> Response:
        """
        Removes a recipe from the user's favorites.

        Args:
            request: The request object.
            pk: The primary key of the recipe to remove from favorites.

        Returns:
            A response indicating success or failure.
        """
        recipe, error = get_recipe_or_error(pk)
        # type: Optional[Recipe], Optional[Response]
        if error:
            return error

        errors: Optional[Response] = uncheck_field_in_user_recipe(
            request.user,
            recipe,
            from_favorited=True,
        )
        if errors:
            return errors

        return Response(status=HTTPStatus.NO_CONTENT)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        renderer_classes=[ShoppingCartRenderer],
    )
    def download_shopping_cart(self, request: Request) -> Response:
        """
        Downloads the user's shopping cart as a PDF.

        Args:
            request: The request object.

        Returns:
            A response with the shopping cart PDF.
        """
        recipes: Recipe = Recipe.objects.filter(
            userrecipe__user=request.user,
            userrecipe__is_in_shopping_cart=True,
        )

        ingredients: RecipeIngredient = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(total=Sum('amount'))
        )

        response: Response = Response(
            data=ingredients,
            headers={
                'Content-Disposition':
                    'attachment; filename="shopping_list.pdf"',
                'Content-Type':
                    'application/pdf; charset=utf-8',
            },
        )

        return response

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def shopping_cart(
            self,
            request: Request,
            pk: int = None,
    ) -> Response:
        """
        Adds a recipe to the user's shopping cart.

        Args:
            request: The request object.
            pk: The primary key of the recipe to add to the shopping cart.

        Returns:
            A response indicating success or failure.
        """
        recipe, error = get_recipe_or_error(pk)
        # type: Optional[Recipe], Optional[Response]
        if error:
            return error

        errors: Optional[Response] = check_field_in_user_recipe(
            request.user,
            recipe,
            is_in_shopping_cart=True,
        )
        if errors:
            return errors

        return Response(
            ShortenedRecipeSerializer(recipe).data,
            status=HTTPStatus.CREATED,
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(
            self,
            request: Request,
            pk: int = None,
    ) -> Response:
        """
        Removes a recipe from the user's shopping cart.

        Args:
            request: The request object.
            pk: The primary key of the recipe to remove from the shopping cart.

        Returns:
            A response indicating success or failure.
        """
        recipe, error = get_recipe_or_error(pk)
        # type: Optional[Recipe], Optional[Response]
        if error:
            return error

        errors: Optional[Response] = uncheck_field_in_user_recipe(
            request.user,
            recipe,
            from_shopping_cart=True,
        )
        if errors:
            return errors

        return Response(status=HTTPStatus.NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """
    A viewset for viewing tags.

    This viewset provides read-only access to the Tag model.
    """
    queryset = Tag.objects.order_by('id')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
