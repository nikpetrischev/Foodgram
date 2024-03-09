# Django Library
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q

from constants import (
    USERNAME_LENGTH,
    PASSWORD_LENGTH,
    EMAIL_LENGTH,
    FIRSTNAME_LENGTH,
    LASTNAME_LENGTH,
)


class CustomUser(AbstractUser):
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

    def __str__(self):
        return f'{self.username}'


class Subscriptions(models.Model):
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
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribe_to'],
                name='unique_subscription',
            ),
            models.CheckConstraint(
                check=~Q(subscriber=F('subscribe_to')),
                name='self_subscription',
            ),
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'

    def __str__(self):
        return f'{self.subscribe_to}'
