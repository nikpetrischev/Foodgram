# Django Library
from django.urls import include, path

# DRF Library
from rest_framework import routers

# Local Imports
from .views import IngredientViewSet, RecipeViewSet, TagViewSet
from users.views import UserModelViewSet

router_v1 = routers.SimpleRouter()
router_v1.register(
    r'users',
    UserModelViewSet,
    basename='users',
)
router_v1.register(
    r'tags',
    TagViewSet,
    basename='tags',
)
router_v1.register(
    r'ingredients',
    IngredientViewSet,
    basename='ingredients',
)
router_v1.register(
    r'recipes',
    RecipeViewSet,
    basename='recipes',
)

urlpatterns = [
    path('', include(router_v1.urls)),
    path(r'auth/', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
]
