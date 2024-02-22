import base64

import webcolors

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import exceptions
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeTag,
    RecipeIngredient,
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


class RecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(
        method_name='get_image_url',
        read_only=True,
    )
    # author = UserSerializer()  # TODO: Update for POST request

    # is_in_shopping_cart = serializers.SerializerMethodField(
    #     required=False,
    #     read_only=True,
    # )

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class RecipeReadSerializer(RecipeSerializer):
    tags = TagSerializer(many=True)
    ingredients = IngredientsReadSerializer(
        source='recipe_with_ingredients',
        many=True,
    )
    is_favorited = serializers.SerializerMethodField(
        required=False,
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
            'is_favorited',
            # 'is_in_shopping_cart',
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

    # def get_is_in_shopping_cart(self, obj):
    #     ...


class RecipeWriteSerializer(RecipeSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
    )
    ingredients = IngredientsWriteSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)

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
        read_only_fields = ('author',)

    def create(self, validated_data):
        # breakpoint()
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

    def to_representation(self, instance):
        return RecipeReadSerializer(instance).data
    #
    # def validate_tags(self, value):
    #     if not value:
    #         return value
    #     tags = Tag.objects.filter(pk__in=value)
    #     if len(tags) != len(value):
    #         raise serializers.ValidationError('Один или более тег не найден')
    #     return value
    #
    #
    # def validate_ingredients(self, value):
    #     ...
