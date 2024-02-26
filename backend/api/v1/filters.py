from django_filters import rest_framework as drf_filters
from django_filters.fields import MultipleChoiceField

from recipes.models import (
    Recipe,
    Ingredient,
)


FLAG_CHOICES = (
    (0, False),
    (1, True),
)


class MultipleCharField(MultipleChoiceField):
    def validate(self, value):
        pass


class MultipleCharFilter(drf_filters.MultipleChoiceFilter):
    field_class = MultipleCharField


class RecipeFilter(drf_filters.FilterSet):
    author = drf_filters.NumberFilter(field_name='author__id')
    tags = MultipleCharFilter(field_name='tags__slug', lookup_expr='contains')
    is_favorited = drf_filters.ChoiceFilter(choices=FLAG_CHOICES)
    is_in_shopping_cart = drf_filters.ChoiceFilter(choices=FLAG_CHOICES)

    class Meta:
        models = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart',
        )


class NameSearchFilter(drf_filters.FilterSet):
    name = drf_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
