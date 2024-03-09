# Standard Library
from http import HTTPStatus

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

    @staticmethod
    def validate_username(value):
        if value == 'me':
            raise ValidationError(
                'Unsupported username. Username cannot be \'me\'',
            )
        return value

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, obj):
        representation = super(UserSerializer, self).to_representation(obj)
        if (request := self.context.get('request')) is not None:
            if (request.method in ('POST',)
                    and 'subscr' not in request.path):
                representation.pop('is_subscribed')
        return representation


class ExpandedUserSerializer(UserSerializer):
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

    def get_recipes(self, obj):
        # Avoiding circular dependencies in DRF Serializers
        # Local Imports
        from api.v1.serializers import ShortenedRecipeSerializer

        query = Recipe.objects.filter(author=obj.id).order_by('id')
        if recipes_limit := self.context.get('recipes_limit'):
            query = query[:int(recipes_limit)]
        serializer = ShortenedRecipeSerializer(query, many=True)
        return serializer.data


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
        fields = (
            'recipe',
            'user',
            'is_favorited',
            'is_in_shopping_cart',
        )


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriptions
        fields = ('subscriber', 'subscribe_to')

    def validate(self, attrs):
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
