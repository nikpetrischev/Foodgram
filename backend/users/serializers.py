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
    is_subscribed = serializers.SerializerMethodField(
        # read_only=True,
        required=False,
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
        )

    def get_is_subscribed(self, obj):
        current_user = self.context.get('request').user
        if isinstance(current_user, AnonymousUser):
            return False
        if '/api/user/me/' in self.context.get('request').path:
            return False
        return Subscriptions.objects.filter(
            subscriber=current_user.id,
            subscribe_to=obj.id,
        ).exists()

    @staticmethod
    def validate_username(value):
        if value == 'me':
            raise ValidationError('Unsupported username. Username cannot be \'me\'')
        return value

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    # def save(self, **kwargs):
    #     self.validated_data.pop('is_subscribed')
    #     return super().save(**kwargs)


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


class ChangePasswordSerializer(serializers.Serializer):
    model = User

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    @staticmethod
    def validate_new_password(value):
        validate_password(value)
        return value
