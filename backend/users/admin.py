# Django Library
from django.contrib import admin

# Local Imports
from .models import CustomUser, Subscriptions


class RecipeInline(admin.StackedInline):
    model = CustomUser.favourites.through
    extra = 1


class SubscriptionInline(admin.TabularInline):
    model = Subscriptions
    fk_name = 'subscriber'
    extra = 1


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email']
    fieldsets = [
        ['Credentials', {
            'fields': ['username', 'email'],
        }],
        ['Name', {
            'fields': ['first_name', 'last_name'],
        }],
    ]
    inlines = [
        RecipeInline,
        SubscriptionInline,
    ]
    search_fields = ['^username', '^email']
    save_on_top = True
