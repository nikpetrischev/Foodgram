# Standard Library
from typing import Any

# Django Library
from django_filters import rest_framework as drf_filters
from django_filters.fields import MultipleChoiceField

# Local Imports
from recipes.models import Ingredient, Recipe

FLAG_CHOICES = (
    (0, False),
    (1, True),
)


class MultipleCharField(MultipleChoiceField):
    """
    A custom field for handling multiple choices in a filter.

    This class overrides the validate method
    to ensure custom validation logic can be applied.
    """
    def validate(self, value: Any) -> None:
        """
        Placeholder for validation logic.

        Args:
            value (Any): The value to validate.

        Raises:
            NotImplementedError: This method is not implemented.
        """
        pass


class MultipleCharFilter(drf_filters.MultipleChoiceFilter):
    """
    A filter for handling multiple character choices in a filter set.

    This class sets the field_class to MultipleCharField,
    allowing for multiple character choices.
    """
    field_class = MultipleCharField


class RecipeFilter(drf_filters.FilterSet):
    """
    A filter set for filtering recipes based on various criteria.

    This filter set includes filters for author, tags,
    is_favorited, and is_in_shopping_cart.
    Supports multiple tag choices.
    """
    author = drf_filters.NumberFilter(field_name='author__id')
    tags = drf_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = drf_filters.ChoiceFilter(
        field_name='userrecipe__is_favorited',
        choices=FLAG_CHOICES,
    )
    is_in_shopping_cart = drf_filters.ChoiceFilter(
        field_name='userrecipe__is_in_shopping_cart',
        choices=FLAG_CHOICES,
    )

    class Meta:
        models = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class NameSearchFilter(drf_filters.FilterSet):
    """
    A filter set for searching ingredients by name.

    This filter set includes a filter for the name field,
    using the 'istartswith' lookup expression.
    """
    name = drf_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
