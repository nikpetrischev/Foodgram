# Django Library
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

# Local Imports
from .mixins import NameAndStrAbstract
from users.models import CustomUser
from constants import (
    MEASUREMENT_UNIT_LENGTH,
    COLOR_LENGTH,
    MIN_COOKING_TIME,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MAX_AMOUNT,
)


class Ingredient(NameAndStrAbstract):
    """
    A model representing an ingredient.

    This model includes fields for the name of the ingredient
    and its measurement unit. It inherits from NameAndStrAbstract,
    which provides a common structure for models
    that have a name and a string representation.
    """
    measurement_unit = models.CharField(
        blank=False,
        null=False,
        max_length=MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единицы измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'ингредиенты'

    def __str__(self):
        """
        Return a string representation of the ingredient.

        Returns
        -------
        str
            A string in the format "name (measurement_unit)".
        """
        return f'{self.name} ({self.measurement_unit})'


class Tag(NameAndStrAbstract):
    """
    A model representing a tag.

    This model includes fields for the name of the tag, a slug for URL-friendly
    identification, and a color represented as a hex code.
    It inherits from NameAndStrAbstract, which provides a common structure
    for models that have a name and a string representation.
    """
    slug = models.SlugField(
        null=False,
        blank=False,
        unique=True,
        verbose_name='Идентификатор',
    )
    color = models.CharField(
        validators=(
            # Requires color code in hex starting with #
            RegexValidator(r'^#[a-fA-F0-9]{6}$'),
        ),
        max_length=COLOR_LENGTH,
        null=False,
        verbose_name='Цвет тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'теги'


class Recipe(NameAndStrAbstract):
    """
    A model representing a recipe.

    This model includes fields for the author, image, text, ingredients,
    tags, and cooking time. It also includes a many-to-many relationship
    with the Ingredient and Tag models through the RecipeIngredient
    and RecipeTag models, respectively.
    """
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
        validators=(
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ),
        blank=False,
        verbose_name='Время на приготовление (мин.)',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'список рецептов'


class RecipeIngredient(models.Model):
    """
    A model representing the relationship between a recipe and an ingredient.

    This model includes fields for the recipe, ingredient,
    and amount of the ingredient used in the recipe.
    It ensures that each recipe-ingredient pair is unique.
    """
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
    amount = models.IntegerField(
        null=False,
        blank=False,
        validators=(
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT),
        ),
        verbose_name='Количество',
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='no_same_ingredients',
            ),
        )
        verbose_name = 'Состав'
        verbose_name_plural = 'состав'

    def __str__(self):
        """
        Return a string representation of the recipe-ingredient relationship.

        Returns
        -------
        str
            A string in the format "ingredient_name: amount measurement_unit".
        """
        return (f'{self.ingredient.name}: '
                + f'{self.amount} {self.ingredient.measurement_unit}')


class RecipeTag(models.Model):
    """
    A model representing the relationship between a recipe and a tag.

    This model includes fields for the recipe and tag. It ensures that each
    recipe-tag pair is unique.
    """
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'tag'),
                name='no_same_tags',
            ),
        )
        verbose_name = 'Теги'
        verbose_name_plural = 'теги'

    def __str__(self):
        """
        Return a string representation of the recipe-tag relationship.

        Returns
        -------
        str
            The name of the tag.
        """
        return self.tag.name


class UserRecipe(models.Model):
    """
    A model representing a user's relationship with a recipe.

    This model includes fields for the user, recipe,
    and flags indicating whether the recipe is favorited
    or in the shopping cart. It ensures that each user-recipe pair is unique.
    """
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

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favourites',
            ),
        )
        verbose_name = 'Рецепт'
        verbose_name_plural = 'избранное'

    def __str__(self):
        """
        Return a string representation of the user-recipe relationship.

        Returns
        -------
        str
            The string representation of the recipe.
        """
        return f'{self.recipe}'
