# Standard Library
from http import HTTPStatus
from typing import Any, Dict

# Django Library
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

# DRF Library
from rest_framework import serializers
from rest_framework.validators import ValidationError

# Local Imports
from .models import Subscriptions
from recipes.models import Recipe, UserRecipe

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    This serializer includes fields for the user's ID, username, email,
    first name, last name, and password. It also includes
    a custom method field for checking if the current user is subscribed
    to another user.
    """
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

    def get_is_subscribed(self, obj: User) -> bool:
        """
        Determine if the current user is subscribed to the user
        represented by `obj`.

        Parameters:
            obj (User): The user object to check subscription status against.

        Returns:
            bool: True if the current user is subscribed to `obj`,
                  False otherwise.
        """
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

    @staticmethod
    def validate_username(value: str) -> str:
        """
        Validate the username field.

        Parameters:
            value (str): The username to validate.

        Returns:
            str: The validated username.

        Raises:
            ValidationError: If the username is 'me'.
        """
        if value == 'me':
            raise ValidationError(
                'Unsupported username. Username cannot be \'me\'',
            )
        return value

    def create(self, validated_data: Dict[str, Any]) -> User:
        """
        Create a new user instance.

        Parameters:
            validated_data (Dict[str, Any]): The validated data for the new
                                             user.

        Returns:
            User: The newly created user instance.
        """
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, obj: User) -> Dict[str, Any]:
        """
        Convert the user object to a dictionary for serialization.

        Parameters:
            obj (User): The user object to serialize.

        Returns:
            Dict[str, Any]: The serialized user data.
        """
        representation = super(UserSerializer, self).to_representation(obj)
        if (request := self.context.get('request')) is not None:
            if (request.method in ('POST',)
                    and 'subscr' not in request.path):
                representation.pop('is_subscribed')
        return representation


class ExpandedUserSerializer(UserSerializer):
    """
    Extended serializer for the User model.

    This serializer includes all fields from the UserSerializer and adds fields
    for the user's recipes and the count of their recipes.
    """
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.ReadOnlyField(
        source='recipes.count',
    )

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

    def get_recipes(self, obj: User) -> list:
        """
        Get the recipes created by the user.

        Parameters:
            obj (User): The user object to get recipes for.

        Returns:
            list: The serialized recipes created by the user.
        """
        # Local Imports
        from api.v1.serializers import ShortenedRecipeSerializer

        query = Recipe.objects.filter(author=obj.id).order_by('id')
        if recipes_limit := self.context.get('recipes_limit'):
            query = query[:int(recipes_limit)]
        serializer = ShortenedRecipeSerializer(query, many=True)
        return serializer.data


class FavouritesOrCartSerializer(serializers.ModelSerializer):
    """
    Serializer for adding or removing recipes from a user's favorites
    or shopping cart.

    This serializer includes fields for the recipe, user, and flags
    for whether the recipe is favorited or in the shopping cart.
    """
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
        fields = (
            'recipe',
            'user',
            'is_favorited',
            'is_in_shopping_cart',
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Subscriptions model.

    This serializer includes fields for the subscriber
    and the user they are subscribing to.
    It also includes validation to ensure that a user cannot subscribe
    to themselves.
    """
    class Meta:
        model = Subscriptions
        fields = ('subscriber', 'subscribe_to')

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the subscription data.

        Parameters:
            attrs (Dict[str, Any]): The data to validate.

        Returns:
            Dict[str, Any]: The validated data.

        Raises:
            ValidationError: If the subscriber and subscribe_to fields are the
                             same, or if the subscription already exists.
        """
        subscriber_id = attrs['subscriber']
        subscribe_to_id = attrs['subscribe_to']

        if subscriber_id == subscribe_to_id:
            raise ValidationError(
                {'errors': 'Подписка на самого себя недопустима'},
                code=HTTPStatus.BAD_REQUEST,
            )

        if Subscriptions.objects.filter(
            subscriber=subscriber_id,
            subscribe_to=subscribe_to_id,
        ):
            raise ValidationError(
                {'errors': 'Подписка уже была оформлена'},
                code=HTTPStatus.BAD_REQUEST,
            )

        return attrs
