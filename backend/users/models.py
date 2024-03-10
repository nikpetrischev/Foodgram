# Django Library
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q

from constants import (
    EMAIL_LENGTH,
    FIRSTNAME_LENGTH,
    LASTNAME_LENGTH,
    PASSWORD_LENGTH,
    USERNAME_LENGTH,
)


class CustomUser(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.

    This model adds additional fields and methods to the default user model.
    It includes fields for username, password, first name, last name,
    and email, as well as relationships for favorites and subscriptions.
    """
    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        null=False,
        blank=False,
        verbose_name='Логин',
        validators=(RegexValidator(r'^[\w.@+-]+\Z'),),
    )
    password = models.CharField(
        max_length=PASSWORD_LENGTH,
        null=False,
        blank=False,
        verbose_name='Пароль',
    )
    first_name = models.CharField(
        max_length=FIRSTNAME_LENGTH,
        null=False,
        blank=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=LASTNAME_LENGTH,
        null=False,
        blank=False,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        null=False,
        blank=False,
        verbose_name='Почта',
    )
    favourites = models.ManyToManyField(
        to='recipes.Recipe',
        through='recipes.UserRecipe',
        blank=True,
        verbose_name='Избранное',
    )
    subscriptions = models.ManyToManyField(
        to='self',
        blank=True,
        symmetrical=False,
        verbose_name='Подписки',
        through='Subscriptions',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'пользователи'

    def __str__(self) -> str:
        """
        Return the username of the user.

        Returns:
            str: The username of the user.
        """
        return f'{self.username}'


class Subscriptions(models.Model):
    """
    Model representing a subscription between users.

    This model defines a many-to-many relationship between users,
    allowing one user to subscribe to another. It includes fields for
    the subscriber and the user they are subscribing to.
    """
    subscriber = models.ForeignKey(
        CustomUser,
        blank=False,
        null=False,
        related_name='subscriber',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    subscribe_to = models.ForeignKey(
        CustomUser,
        blank=False,
        null=False,
        related_name='subscribe_to',
        on_delete=models.CASCADE,
        verbose_name='Подписка на пользователя',
    )
    objects = models.Manager()

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('subscriber', 'subscribe_to'),
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F('subscribe_to')),
                name='self_subscription',
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def __str__(self) -> str:
        """
        Return the username of the user being subscribed to.

        Returns:
            str: The username of the user being subscribed to.
        """
        return f'{self.subscribe_to}'
