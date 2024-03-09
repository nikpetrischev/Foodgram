# Django Library
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from rest_framework.authtoken.models import TokenProxy

# Local Imports
from .models import CustomUser, Subscriptions

from recipes.models import Recipe, UserRecipe


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


class RecipeInline(admin.StackedInline):
    model = CustomUser.favourites.through
    extra = 1


class SubscriptionInline(admin.TabularInline):
    model = Subscriptions
    fk_name = 'subscriber'
    extra = 1


@admin.register(CustomUser)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email')
    fieldsets = (
        ('Credentials', {
            'fields': ('username', 'email', 'password'),
        }),
        ('Name', {
            'fields': ('first_name', 'last_name'),
        }),
        ('Other data', {
            'fields': (
                'count_recipes',
                'count_subscriptions',
                'count_favorites',
            ),
        }),
    )
    readonly_fields = (
        'count_recipes',
        'count_subscriptions',
        'count_favorites',
    )
    inlines = (
        RecipeInline,
        SubscriptionInline,
    )
    search_fields = ('^username', '^email')
    save_on_top = True

    @admin.display(description='Кол-во подписок')
    def count_subscriptions(self, obj):
        return Subscriptions.objects.filter(subscriber=obj.id).count()

    @admin.display(description='Рецептов в избранном')
    def count_favorites(self, obj):
        return UserRecipe.objects.filter(
            user=obj.id,
            is_favorited=True,
        ).count()

    @admin.display(description='Своих рецептов в базе')
    def count_recipes(self, obj):
        return Recipe.objects.filter(author=obj.id).count()
