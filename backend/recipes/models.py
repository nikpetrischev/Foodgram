from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from users.models import CustomUser
from .Mixins import NameAndStrAbstract


class Ingredient(NameAndStrAbstract):
    measurement_unit = models.CharField(
        blank=False,
        null=False,
        max_length=32,
        verbose_name='Единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Tag(NameAndStrAbstract):
    slug = models.SlugField(
        null=False,
        blank=False,
        unique=True,
        verbose_name='Идентификатор',
    )
    color = models.CharField(
        validators=[
            # Requires color code in hex starting with #
            RegexValidator(r'^#[a-fA-F0-9]{6}$'),
        ],
        max_length=7,
        null=False,
        verbose_name='Цвет тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'


class Recipe(NameAndStrAbstract):
    author = models.ForeignKey(
        to=CustomUser,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
    )
    image = models.ImageField(
        null=False,
        blank=False,
        default=None,
        upload_to='recipes/images/',
        verbose_name='Иллюстрация',
    )
    text = models.TextField(
        null=False,
        blank=False,
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        to=Ingredient,
        through='RecipeIngredient',
        verbose_name='Состав',
    )
    tags = models.ManyToManyField(
        to=Tag,
        through='RecipeTag',
        verbose_name='Список тегов',
    )
    cooking_time = models.IntegerField(
        null=False,
        validators=[MinValueValidator(1)],
        blank=False,
        verbose_name='Время на приготовление (мин.)',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'список рецептов'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_with_ingredients',
    )
    ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_for_recipe',
    )
    amount = models.FloatField(
        null=False,
        blank=False,
        validators=[MinValueValidator(0)],
        verbose_name='Количество',
    )
    objects = models.Manager()

    def __str__(self):
        ingredient = Ingredient.objects.get(pk=self.ingredient.id)
        return (f'{ingredient.name}: '
                + f'{self.amount} {ingredient.measurement_unit}')


class RecipeTag(models.Model):
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE,
    )
    objects = models.Manager()


class UserRecipe(models.Model):
    user = models.ForeignKey(
        to=CustomUser,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        to=Recipe,
        blank=False,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    is_favorited = models.BooleanField(
        verbose_name='В избранном',
        default=False,
    )
    is_in_shopping_cart = models.BooleanField(
        verbose_name='В корзине',
        default=False,
    )
    objects = models.Manager

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favourites',
            )
        ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'избранное'

    def __str__(self):
        return f'{self.recipe}'
