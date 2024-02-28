# Django Library
from django.contrib import admin

# Local Imports
from .models import CustomUser, Subscriptions


class RecipeInline(admin.StackedInline):
    model = CustomUser.favourites.through
    extra = 0


class SubscriptionInline(admin.TabularInline):
    model = Subscriptions
    fk_name = 'subscriber'
    extra = 0


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    fieldsets = [
        [None, {
            'fields': ['username', 'first_name', 'last_name'],
        }],
        ['Credentials', {
            'fields': ['email', 'password'],
        }],
    ]
    inlines = [
        RecipeInline,
        SubscriptionInline]
    exclude = ['favourites', 'subscriptions']
