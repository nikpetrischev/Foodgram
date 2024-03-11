# Django Library
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

# DRF Library
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
        (
            'Данные пользователя', {
                'fields': ('username', 'email', 'password'),
            },
        ),
        (
            'Личные данные', {
                'fields': ('first_name', 'last_name'),
            },
        ),
        (
            'Прочее', {
                'fields': (
                    'count_recipes',
                    'count_subscriptions',
                    'count_favorites',
                ),
            },
        ),
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
        # return Subscriptions.objects.filter(subscriber=obj.id).count()
        return obj.subscriptions.count()

    @admin.display(description='Рецептов в избранном')
    def count_favorites(self, obj):
        return UserRecipe.objects.filter(
            user=obj.id,
            is_favorited=True,
        ).count()
        # return obj.favourites.count()

    @admin.display(description='Своих рецептов в базе')
    def count_recipes(self, obj):
        return obj.recipes.count()


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'subscriber', 'subscribe_to')
    ordering = ('pk',)
    fields = (('subscriber',), ('subscribe_to', 'get_subs_recipes'))
    search_fields = ('^subscriber__username', '^subscribe_to__username')

    @admin.display(description='Кол-во рецептов')
    def get_subs_recipes(self, obj):
        return obj.subscribe_to.recipes.count()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False
