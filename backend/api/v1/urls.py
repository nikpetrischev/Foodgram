from django.urls import include, path

from rest_framework import routers

from users.views import UserModelViewSet
from .views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
)

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
# router_v1.register(
#     r'user/(?P<id>\d+)/subscribe',
#     ...,
#     basename='subscribe',
# )

urlpatterns = [
    path('', include(router_v1.urls)),
    path(r'auth/', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
]
