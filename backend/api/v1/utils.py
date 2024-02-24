from django_filters import rest_framework as drf_filters

from rest_framework import filters

from recipes.models import (
    RecipeTag,
    Recipe,
    Ingredient,
)
from users.models import CustomUser


FLAG_CHOICES = (
    (0, False),
    (1, True),
)


class RecipeFilter(drf_filters.FilterSet):
    author = drf_filters.NumberFilter(field_name='id')
    tags = drf_filters.CharFilter(field_name='tags__slug')
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
    # def get_search_fields(self, view, request):
    #     if request.query_params.get('name'):
    #         return ['^name']
    #     return super().get_search_fields(view, request)
