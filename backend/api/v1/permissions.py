# DRF Library
from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import View

# Local Imports
from recipes.models import Recipe


class AuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission class for Recipe model.
    """

    def has_permission(self, request: Request, view: View) -> bool:
        """
        Check if the request has permission to perform the action.

        Args:
            request (Request): The request instance.
            view (View): The view instance.

        Returns:
            bool: True if the request method is in SAFE_METHODS,
            False otherwise.
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
        Check if the request has permission to perform the action
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
