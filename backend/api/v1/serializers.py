# Standard Library
from http import HTTPStatus
from typing import Any, Union

# Django Library
from django.contrib.auth import get_user_model

# DRF Library
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from constants import MAX_AMOUNT, MIN_AMOUNT

# Local Imports
from .fields import Hex2NameColorField, Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag
from users.serializers import UserSerializer

User = get_user_model()


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
    color = Hex2NameColorField(required=True, allow_null=False)
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
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={
            'does_not_exist': 'Ингредиента в базе не найдено',
        },
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'max_value': 'Кол-во ингредиента выше максимума',
            'min_value': 'Кол-во ингредиента ниже минимума',
        },
    )

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

    def get_image_url(self, obj: Recipe) -> Union[str, None]:
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
        ordering = ('id',)


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
            user_recipe = (obj.userrecipe_set
                           .get(user=self.context.get('request').user.id))
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
            user_recipe = (obj.userrecipe_set
                           .get(user=self.context.get('request').user.id))
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
        extra_kwargs = {
            'name': {
                'validators': (
                    UniqueValidator(
                        queryset=Recipe.objects.all(),
                        message='Рецепт с таким именем уже существует',
                    ),
                ),
            },
        }

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
        recipe: Recipe = super().create(validated_data)

        self.set_recipe_tag(recipe, tags)

        self.set_recipe_ingredient(recipe, ingredients)

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

        ingredients: dict = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.set_recipe_ingredient(instance, ingredients)

        tags: list = validated_data.pop('tags')
        RecipeTag.objects.filter(recipe=instance).delete()
        self.set_recipe_tag(instance, tags)

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

    def validate_ingredients(self, value: list) -> list:
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
        if not value:
            raise serializers.ValidationError(
                'Поле \'Ингредиенты\' обязательно',
                code=HTTPStatus.BAD_REQUEST,
            )

        ingredients = {v['id'] for v in value}
        if len(ingredients) != len(value):
            raise serializers.ValidationError(
                'Повтор ингредиента',
                code=HTTPStatus.BAD_REQUEST,
            )

        return value

    def validate_tags(self, value: list) -> list:
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
        if not value:
            raise serializers.ValidationError(
                'Поле \'Теги\' обязательно',
                code=HTTPStatus.BAD_REQUEST,
            )

        tag_ids = {v.id for v in value}
        if len(tag_ids) != len(value):
            raise serializers.ValidationError(
                'Повтор тега',
                code=HTTPStatus.BAD_REQUEST,
            )

        return value

    def set_recipe_tag(self, recipe, tags):
        recipe_tag = [RecipeTag(tag=tag, recipe=recipe) for tag in tags]
        RecipeTag.objects.bulk_create(recipe_tag)

    def set_recipe_ingredient(self, recipe, ingredients):
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
