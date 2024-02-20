from django.contrib import admin
from .models import (
    Recipe,
    Tag,
    Ingredient,
)


class TagInline(admin.StackedInline):
    model = Recipe.tags.through
    extra = 0


class IngredientsInline(admin.StackedInline):
    model = Recipe.ingredients.through
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = [TagInline, IngredientsInline]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass
