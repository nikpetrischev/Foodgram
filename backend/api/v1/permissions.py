# DRF Library
from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

# Local Imports
from recipes.models import Recipe


class AuthorOrAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission class for the Recipe model.

    This permission class allows any authenticated user to perform
    read-only actions (GET, HEAD, OPTIONS) on any recipe.
    It also allows a user to modify a recipe
    if they are the author of that recipe.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Determine if the request has permission to perform the action.

        Args:
            request (Request): The request instance.
            view (View): The view instance.

        Returns:
            bool: True if the request method is in SAFE_METHODS
            or the user is authenticated, False otherwise.
        """
        return (request.method in SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(
            self,
            request: Request,
            view: View,
            obj: Recipe,
    ) -> bool:
        """
        Determine if the request has permission to perform the action
        on the given object.

        Args:
            request (Request): The request instance.
            view (View): The view instance.
            obj (Recipe): The object the request is acting upon.

        Returns:
            bool: True if the request method is in SAFE_METHODS
            or the object's author is the request user, False otherwise.
        """
        return obj.author == request.user or request.method in SAFE_METHODS
