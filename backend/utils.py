# Standard Library
from http import HTTPStatus
from typing import Optional, Union

# DRF Library
from rest_framework.response import Response

# Local Imports
from recipes.models import Recipe, RecipeIngredient, RecipeTag, UserRecipe
from users.models import CustomUser
from users.serializers import FavouritesOrCartSerializer


def error_response(
        error_message: Union[str, dict, None] = None,
        status_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
) -> Response:
    """
    Generate response with zero or more implicit errors and status code.
    """
    if isinstance(error_message, dict):
        response: Response = Response(data=error_message, status=status_code)
    else:
        response: Response = (
            Response(
                data={'errors': error_message},
                status=status_code,
            )
            if error_message else Response(status=status_code)
        )
    return response


def get_recipe_or_error(
        pk: int,
        suggested_error_code: HTTPStatus = HTTPStatus.NOT_FOUND,
) -> tuple[Optional[Recipe], Optional[Response]]:
    """
    Fetch a recipe by its primary key
    or return an error response if not found.
    """
    recipe: Recipe = Recipe.objects.filter(pk=pk).first()
    if not recipe:
        return None, error_response(
            error_message='Рецепт не найден',
            status_code=suggested_error_code,
        )
    return recipe, None


def check_field_in_user_recipe(
        user: CustomUser,
        recipe: Recipe,
        is_favorited: Optional[bool] = None,
        is_in_shopping_cart: Optional[bool] = None,
) -> Union[Response, None]:
    """
    Check favorited or shopping cart status of UserRecipe instance
    for the given user and recipe.
    """
    user_recipe: UserRecipe
    user_recipe, _ = (UserRecipe.objects
                      .get_or_create(user=user, recipe=recipe))

    data: dict = {}
    if is_favorited is not None:
        if user_recipe.is_favorited:
            return error_response(f'{recipe.name} уже в избранном')
        data['is_favorited'] = True
    if is_in_shopping_cart is not None:
        if user_recipe.is_in_shopping_cart:
            return error_response(f'{recipe.name} уже в корзине')
        data['is_in_shopping_cart'] = True

    serializer: FavouritesOrCartSerializer
    serializer = FavouritesOrCartSerializer(
        user_recipe,
        data=data,
        partial=True,
    )
    if serializer.is_valid():
        serializer.save()
        return None

    return error_response(serializer.errors)


def uncheck_field_in_user_recipe(
        user: CustomUser,
        recipe: Recipe,
        from_favorited: Optional[bool] = None,
        from_shopping_cart: Optional[bool] = None,
) -> Union[Response, None]:
    """
    Uncheck favorited or shopping cart status of UserRecipe instance
    for the given user and recipe.
    """
    fields: dict = {}
    if from_favorited:
        fields['is_favorited'] = True
    if from_shopping_cart:
        fields['is_in_shopping_cart'] = True

    user_recipe: UserRecipe = UserRecipe.objects.filter(
        **fields,
        user=user,
        recipe=recipe,
    ).first()
    if not user_recipe:
        return error_response(f'{recipe.name} не был отмечен')

    data: dict = {}
    if from_favorited is not None:
        if not user_recipe.is_favorited:
            return error_response(f'{recipe.name} нет в избранном')
        data['is_favorited'] = False
    if from_shopping_cart is not None:
        if not user_recipe.is_in_shopping_cart:
            return error_response(f'{recipe.name} нет в корзине')
        data['is_in_shopping_cart'] = False

    serializer: FavouritesOrCartSerializer
    serializer = FavouritesOrCartSerializer(
        user_recipe,
        data=data,
        partial=True,
    )
    if serializer.is_valid():
        serializer.save()
        return None

    return error_response(serializer.errors)


def check_favorite_or_cart(
        pk,
        request,
        is_favorited=None,
        is_in_shopping_cart=None,
):
    # Evading circular importing
    # Local Imports
    from api.v1.serializers import ShortenedRecipeSerializer

    recipe, error = get_recipe_or_error(pk, HTTPStatus.BAD_REQUEST)
    # type: Optional[Recipe], Optional[Response]
    if error:
        return error
    errors: Optional[Response] = check_field_in_user_recipe(
        request.user,
        recipe,
        is_favorited,
        is_in_shopping_cart,
    )
    if errors:
        return errors
    return Response(
        ShortenedRecipeSerializer(recipe).data,
        status=HTTPStatus.CREATED,
    )


def uncheck_favorite_or_cart(
        pk,
        request,
        from_favorited=None,
        from_shopping_cart=None,
):
    recipe, error = get_recipe_or_error(pk)
    # type: Optional[Recipe], Optional[Response]
    if error:
        return error

    errors: Optional[Response] = uncheck_field_in_user_recipe(
        request.user,
        recipe,
        from_favorited,
        from_shopping_cart,
    )
    if errors:
        return errors

    return Response(status=HTTPStatus.NO_CONTENT)


def set_recipe_tag(recipe, tags):
    recipe_tag = [RecipeTag(tag=tag, recipe=recipe) for tag in tags]
    RecipeTag.objects.bulk_create(recipe_tag)


def set_recipe_ingredient(recipe, ingredients):
    recipe_ingredient = [
        RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient.get('id'),
            amount=ingredient.get('amount'),
        ) for ingredient in ingredients
    ]
    # Sorting by name
    recipe_ingredient.sort(key=lambda x: x.ingredient.name)
    RecipeIngredient.objects.bulk_create(recipe_ingredient)
