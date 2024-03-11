# Django Library
from django_filters import rest_framework as drf_filters

# Local Imports
from recipes.models import Ingredient, Recipe

FLAG_CHOICES = (
    (0, False),
    (1, True),
)


class RecipeFilter(drf_filters.FilterSet):
    """
    A filter set for filtering recipes based on various criteria.

    This filter set includes filters for author, tags,
    is_favorited, and is_in_shopping_cart.
    Supports multiple tag choices.
    """
    tags = drf_filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = drf_filters.ChoiceFilter(
        field_name='userrecipe__is_favorited',
        choices=FLAG_CHOICES,
        method='check_favorite_or_cart',
    )
    is_in_shopping_cart = drf_filters.ChoiceFilter(
        field_name='userrecipe__is_in_shopping_cart',
        choices=FLAG_CHOICES,
        method='check_favorite_or_cart',
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def check_favorite_or_cart(self, queryset, name, value):
        if self.request.user.is_authenticated:
            return queryset.filter(
                **{
                    'userrecipe__user': self.request.user,
                    name: value,
                },
            )
        return queryset.filter(**{name: value})


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
