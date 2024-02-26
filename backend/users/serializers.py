from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import Recipe, UserRecipe

from .models import Subscriptions

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    id = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        if (request := self.context.get('request')) is None:
            return False
        current_user = request.user
        if isinstance(current_user, AnonymousUser):
            return False
        if '/api/user/me/' in request.path:
            return False
        return Subscriptions.objects.filter(
            subscriber=current_user.id,
            subscribe_to=obj.id,
        ).exists()

    def validate_username(self, value):
        if value == 'me':
            raise ValidationError('Unsupported username. Username cannot be \'me\'')
        return value

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, obj):
        representation = super(UserSerializer, self).to_representation(obj)
        if (request := self.context.get('request')) is not None:
            if (request.method in ['POST']
                    and 'subscr' not in request.path):
                representation.pop('is_subscribed')
        return representation


class ExpandedUserSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        # Avoiding circular dependencies in DRF Serializers
        from api.v1.serializers import ShortenedRecipeSerializer

        query = Recipe.objects.filter(author=obj.id).order_by('id')
        if recipes_limit := self.context.get('recipes_limit'):
            query = query[:int(recipes_limit)]
        serializer = ShortenedRecipeSerializer(query, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavouritesOrCartSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
    )
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = UserRecipe
        fields = [
            'recipe',
            'user',
            'is_favorited',
            'is_in_shopping_cart',
        ]

#cd pos
# class ChangePasswordSerializer(serializers.Serializer):
#     model = User
#
#     current_password = serializers.CharField(required=True)
#     new_password = serializers.CharField(required=True)
#
#     @staticmethod
#     def validate_new_password(value):
#         validate_password(value)
#         return value
