# Standard Library
import base64
from typing import Any, Union

# Django Library
from django.contrib.auth import get_user_model
from django.core import exceptions
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

# DRF Library
from rest_framework import serializers

import webcolors

# Local Imports
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeTag,
    Tag,
    UserRecipe,
)
from users.serializers import UserSerializer

User = get_user_model()


class Hex2NameColor(serializers.Field):
    """
    A custom serializer field to convert hex color codes to their names.

    This field is used to validate and convert hex color codes
    to their corresponding color names using the `webcolors` library.
    """

    def to_representation(self, value: str) -> str:
        """
        Display color's hex value.

        Parameters
        ----------
        value : str
            The internal color's value.

        Returns
        -------
        str
            The represented value.
        """
        return value

    def to_internal_value(self, data: str) -> str:
        """
        Convert the input data to the internal value.

        Parameters
        ----------
        data : str
            The input data to convert.

        Returns
        -------
        str
            The converted internal value.

        Raises
        ------
        serializers.ValidationError
            If the input data cannot be converted to a color name.
        """
        try:
            data: str = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Не найдено имя для цвета')
        return data


class Base64ImageField(serializers.ImageField):
    """
    A custom serializer field for handling base64 encoded images.

    This field is used to validate and convert base64 encoded image strings to
    Django ContentFile objects.
    """

    def to_internal_value(self, data: str) -> ContentFile:
        """
        Validate and convert the input data to the internal value.

        Parameters
        ----------
        data : str
            The input data to validate and convert.

        Returns
        -------
        ContentFile
            The converted internal value.

        Raises
        ------
        serializers.ValidationError
            If the input data is not a valid base64 encoded image.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    """
    A serializer for the Ingredient model.

    This serializer includes the id, name,
    and measurement_unit fields of the Ingredient model.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """
    A serializer for the Tag model.

    This serializer includes the id, name, slug, and color fields
    of the Tag model. The color field uses the Hex2NameColor field
    for validation and conversion.
    """
    color = Hex2NameColor(required=True, allow_null=False)
    slug = serializers.SlugField(required=True, allow_null=False)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientsReadSerializer(serializers.ModelSerializer):
    """
    A read-only serializer for the RecipeIngredient model.

    This serializer includes the id, name, and measurement_unit fields
    of the Ingredient model through the RecipeIngredient model.
    It is used for read operations to display the ingredients
    associated with a recipe.
    """
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsWriteSerializer(serializers.ModelSerializer):
    """
    A write-only serializer for the RecipeIngredient model.

    This serializer includes the id and amount fields
    of the RecipeIngredient model.
    The id field is used to reference the Ingredient model.
    It is used for write operations to create or update ingredients associated
    with a recipe.
    """
    id = serializers.IntegerField(source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class AbstractRecipeSerializer(serializers.ModelSerializer):
    """
    An abstract base serializer for the Recipe model.

    This serializer includes a method to get the image URL.
    It is intended to be subclassed by other serializers
    that need to serialize recipe data.
    """
    image = serializers.SerializerMethodField(
        method_name='get_image_url',
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = '__all__'

    @staticmethod
    def get_image_url(obj: Recipe) -> Union[str, None]:
        """
        Get the URL of the recipe's image.

        Parameters
        ----------
        obj : Recipe
            The recipe instance.

        Returns
        -------
        str
            The URL of the recipe's image, or None if no image is set.
        """
        if obj.image:
            return obj.image.url
        return None


class ShortenedRecipeSerializer(AbstractRecipeSerializer):
    """
    A serializer for the Recipe model with a shortened set of fields.

    This serializer includes a subset of the fields available
    in the Recipe model, focusing on essential information such as
    id, name, image, and cooking_time. It is used for operations
    where a concise representation of the recipe is needed.
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
        ordering = ['id']


class RecipeReadSerializer(AbstractRecipeSerializer):
    """
    A serializer for the Recipe model with additional fields
    for read operations.

    This serializer includes fields for tags, ingredients,
    and user-specific information such as whether the recipe is favorited
    or in the shopping cart. It is used for read operations
    to display detailed recipe information along with user-specific data.
    """
    tags = TagSerializer(many=True)
    ingredients = IngredientsReadSerializer(
        source='recipe_with_ingredients',
        many=True,
    )
    is_favorited = serializers.SerializerMethodField(
        required=False,
        read_only=True,
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        required=False,
        read_only=True,
    )
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj: Recipe) -> bool:
        """
        Determine if the recipe is favorited by the current user.

        Parameters
        ----------
        obj : Recipe
            The recipe instance.

        Returns
        -------
        bool
            True if the recipe is favorited by the current user,
            False otherwise.
        """
        try:
            user = self.context.get('request').user
            user_recipe = UserRecipe.objects.get(
                recipe=obj.id,
                user=user.id,
            )
        # Using wide Exception because it doesn't matter which one we get.
        # Any Exception will mean that recipe is not favorited at the least.
        except Exception:
            return False
        else:
            return user_recipe.is_favorited

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        """
        Determine if the recipe is in the current user's shopping cart.

        Parameters
        ----------
        obj : Recipe
            The recipe instance.

        Returns
        -------
        bool
            True if the recipe is in the current user's shopping cart,
            False otherwise.
        """
        try:
            user = self.context.get('request').user
            user_recipe = UserRecipe.objects.get(
                recipe=obj.id,
                user=user.id,
            )
        # Using wide Exception because it doesn't matter which one we get.
        # Any Exception will mean that recipe is not in cart at the least.
        except Exception:
            return False
        else:
            return user_recipe.is_in_shopping_cart


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    A serializer for creating and updating Recipe instances.

    This serializer includes fields for tags, ingredients, image, and author.
    It handles the creation and updating of Recipe instances, including the
    association of tags and ingredients.
    """
    tags = serializers.PrimaryKeyRelatedField(
        required=True,
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientsWriteSerializer(required=True, many=True)
    image = Base64ImageField(required=True)
    author = UserSerializer(
        default=serializers.CurrentUserDefault(),
        read_only=True,
    )

    class Meta:
        model = Recipe
        fields = (
            'name',
            'author',
            'image',
            'text',
            'tags',
            'ingredients',
            'cooking_time',
        )

    def save(self, **kwargs: Any) -> Recipe:
        """
                Save the Recipe instance.

                This method sets the author of the Recipe instance
                to the current user if it's not already set
                and then calls the superclass's save method.

                Parameters
                ----------
                **kwargs : Any
                    Additional keyword arguments.

                Returns
                -------
                Recipe
                    The saved Recipe instance.
                """
        if self.fields['author'] is None:
            kwargs['author'] = self.fields['author'].get_default()
        return super().save(**kwargs)

    def create(self, validated_data: dict) -> Recipe:
        """
        Create a new Recipe instance.

        This method creates a new Recipe instance and associates it with the
        provided tags and ingredients.

        Parameters
        ----------
        validated_data : dict
            The validated data for the new Recipe instance.

        Returns
        -------
        Recipe
            The created Recipe instance.
        """
        tags: list = validated_data.pop('tags')
        ingredients: dict = validated_data.pop('ingredients')
        recipe: Recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            RecipeTag.objects.create(
                recipe=recipe,
                tag=tag,
            )
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient,
                pk=ingredient.get('ingredient'),
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient.get('amount'),
            )
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        """
        Update an existing Recipe instance.

        This method updates the fields of an existing Recipe instance and
        re-associates it with the provided tags and ingredients.

        Parameters
        ----------
        instance : Recipe
            The Recipe instance to update.
        validated_data : dict
            The validated data for the update.

        Returns
        -------
        Recipe
            The updated Recipe instance.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time,
        )
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)

        if 'ingredients' in validated_data:
            ingredients: dict = validated_data.pop('ingredients')
            for ingredient in ingredients:
                ingredient_obj = get_object_or_404(
                    Ingredient,
                    pk=ingredient.get('ingredient'),
                )
                curr_ingredient, _ = RecipeIngredient.objects.get_or_create(
                    recipe=instance,
                    ingredient=ingredient_obj,
                    amount=ingredient.get('amount'),
                )

        if 'tags' in validated_data:
            tags: list = validated_data.pop('tags')
            for tag in tags:
                current_tag, _ = RecipeTag.objects.get_or_create(
                    recipe=instance,
                    tag=tag,
                )

        instance.save()
        return instance

    def to_representation(self, instance: Recipe) -> dict:
        """
        Convert the Recipe instance to a representation suitable for display.

        Parameters
        ----------
        instance : Recipe
            The Recipe instance to convert.

        Returns
        -------
        dict
            The converted representation of the Recipe instance.
        """
        return RecipeReadSerializer(instance).data

    @staticmethod
    def validate_ingredients(value: list) -> list:
        """
        Validate the ingredients field.

        This method checks that the ingredients field is not empty and that
        each ingredient exists in the database. It also ensures that each
        ingredient is unique and that the amount is at least 1.

        Parameters
        ----------
        value : list
            The list of ingredients to validate.

        Returns
        -------
        list
            The validated list of ingredients.

        Raises
        ------
        serializers.ValidationError
            If the ingredients field is empty, an ingredient does not exist in
            the database, an ingredient is repeated,
            or the amount is less than 1.
        """
        if not value or value == []:
            raise serializers.ValidationError(
                'Поле \'Ингредиенты\' обязательно',
                code=400,
            )
        ingredient_ids: list = []
        for ingredient in value:
            try:
                Ingredient.objects.get(
                    pk=ingredient['ingredient'],
                )
            except exceptions.ObjectDoesNotExist:
                raise serializers.ValidationError(
                    'Ингредиент не найден в базе',
                    code=400,
                )
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Минимальное кол-во ингредиента - 1',
                    code=400,
                )
            if ingredient['ingredient'] in ingredient_ids:
                raise serializers.ValidationError(
                    'Повтор ингредиента',
                    code=400,
                )
            else:
                ingredient_ids.append(ingredient['ingredient'])
        return value

    @staticmethod
    def validate_tags(value: list) -> list:
        """
        Validate the tags field.

        This method checks that the tags field is not empty and that each tag
        exists in the database. It also ensures that each tag is unique.

        Parameters
        ----------
        value : list
            The list of tags to validate.

        Returns
        -------
        list
            The validated list of tags.

        Raises
        ------
        serializers.ValidationError
            If the tags field is empty, a tag does not exist in the database,
            or a tag is repeated.
        """
        if not value or value == []:
            raise serializers.ValidationError(
                'Поле \'Теги\' обязательно',
                code=400,
            )
        tag_ids: list = []
        for tag in value:
            try:
                Tag.objects.get(
                    pk=tag.id,
                )
            except exceptions.ObjectDoesNotExist:
                raise serializers.ValidationError(
                    'Тег не найден в базе',
                    code=400,
                )
            if tag.id in tag_ids:
                raise serializers.ValidationError(
                    'Повтор тега',
                    code=400,
                )
            else:
                tag_ids.append(tag.id)
        return value
