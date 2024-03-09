# Django Library
from django.contrib import admin
from django.utils.html import format_html

# Local Imports
from .forms import AtLeastOneRequiredInlineFormSet, TagAdminForm
from .models import Ingredient, Recipe, Tag, UserRecipe


class TagInline(admin.StackedInline):
    formset = AtLeastOneRequiredInlineFormSet
    model = Recipe.tags.through
    extra = 0


class IngredientsInline(admin.StackedInline):
    formset = AtLeastOneRequiredInlineFormSet
    model = Recipe.ingredients.through
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('colored_name',)
    fields = ('name', 'slug', 'color')
    form = TagAdminForm

    @admin.display(description='Тег')
    def colored_name(self, obj):
        return format_html(
            f'<span style="color: {obj.color};">{obj.name}</span>',
        )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fields = (
        'author',
        ('name', 'image', 'text'),
        'cooking_time',
        'count_subscribers',
    )
    readonly_fields = ('count_subscribers',)
    inlines = (TagInline, IngredientsInline)
    list_display = ('name', 'author')
    list_filter = (
        ('author', admin.RelatedOnlyFieldListFilter),
        'name',
        ('tags', admin.RelatedOnlyFieldListFilter),
    )
    list_select_related = ('author',)
    save_on_top = True
    search_fields = ('name',)

    @admin.display(description='Кол-во подписок на рецепт')
    def count_subscribers(self, obj):
        return UserRecipe.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(UserRecipe)
class CartsAndFavoritesAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recipe',
        'favourited',
        'in_shopping_cart',
    )
    list_filter = ('user',)

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
        return request.user.is_staff
