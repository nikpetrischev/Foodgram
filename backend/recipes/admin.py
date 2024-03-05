# Django Library
from django.contrib import admin

# Local Imports
from .models import Ingredient, Recipe, Tag, UserRecipe


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
    fields = [
        'author',
        ('name', 'image', 'text'),
        'cooking_time',
        'count_subscribers',
    ]
    readonly_fields = ['count_subscribers']
    inlines = [TagInline, IngredientsInline]
    list_display = ['name', 'author']
    list_filter = [
        ('author', admin.RelatedOnlyFieldListFilter),
        'name',
        ('tags', admin.RelatedOnlyFieldListFilter),
    ]
    list_select_related = ['author']
    save_on_top = True

    def count_subscribers(self, obj):
        return UserRecipe.objects.filter(recipe=obj).count()
    count_subscribers.short_description = 'Кол-во подписок на рецепт'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']


@admin.register(UserRecipe)
class CartsAndFavoritesAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'recipe',
        'favourited',
        'in_shopping_cart',
    ]
    list_filter = ['user']

    @admin.display(
        boolean=True,
        description='В избранном?'
    )
    def favourited(self, obj):
        return obj.is_favorited

    @admin.display(
        boolean=True,
        description='Добавлено в корзину?'
    )
    def in_shopping_cart(self, obj):
        return obj.is_in_shopping_cart

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
