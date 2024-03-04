# Standart Library
# Standard Library
import base64

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
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Не найдено имя для цвета')
        return data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    color = Hex2NameColor(required=True, allow_null=False)
    slug = serializers.SlugField(required=True, allow_null=False)

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color')


class IngredientsReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class AbstractRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(
        method_name='get_image_url',
        read_only=True,
    )
    # author = UserSerializer()  # TODO: Update for POST request

    class Meta:
        model = Recipe
        fields = '__all__'

    @staticmethod
    def get_image_url(obj):
        if obj.image:
            return obj.image.url
        return None


class ShortenedRecipeSerializer(AbstractRecipeSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')
        ordering = ['id']


class RecipeReadSerializer(AbstractRecipeSerializer):
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

    def get_is_favorited(self, obj):
        # try/except block used because if any of user and/or user_recipe
        # would raise any exception then it means we either don't have any
        # m2m links between current user and recipe or user is unauthorized.
        try:
            user = self.context.get('request').user
            user_recipe = UserRecipe.objects.get(
                recipe=obj.id,
                user=user.id,
            )
        except Exception:
            return False
        else:
            return user_recipe.is_favorited

    def get_is_in_shopping_cart(self, obj):
        try:
            user = self.context.get('request').user
            user_recipe = UserRecipe.objects.get(
                recipe=obj.id,
                user=user.id,
            )
        except Exception:
            return False
        else:
            return user_recipe.is_in_shopping_cart


class RecipeWriteSerializer(AbstractRecipeSerializer):
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

    def save(self, **kwargs):
        if self.fields['author'] is None:
            kwargs['author'] = self.fields['author'].get_default()
        return super().save(**kwargs)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
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

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time,
        )
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)

        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
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
            tags = validated_data.pop('tags')
            for tag in tags:
                current_tag, _ = RecipeTag.objects.get_or_create(
                    recipe=instance,
                    tag=tag,
                )

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data

    @staticmethod
    def validate_ingredients(value):
        if not value or value == []:
            raise serializers.ValidationError(
                'Поле \'Ингредиенты\' обязательно',
                code=400,
            )
        ingredient_ids = []
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
    def validate_tags(value):
        if not value or value == []:
            raise serializers.ValidationError(
                'Поле \'Теги\' обязательно',
                code=400,
            )
        tag_ids = []
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
