# DRF Library
from rest_framework import permissions


class RecipePermission(permissions.BasePermission):
    """
    A custom permission class for handling permissions on recipe-related views.

    This class extends the BasePermission class from Django Rest Framework
    to define custom permission checks for recipe-related views. It allows
    authenticated users to perform any request and ensures that only the author
    of a recipe or users performing safe methods (GET, HEAD, OPTIONS)
    can access or modify the recipe.
    """

    def has_permission(self, request, view):
        """
        Determines if the request has permission to access the view.

        This method checks if the request method is a safe method
        (GET, HEAD, OPTIONS) or if the user is authenticated.
        Safe methods are allowed for all users,
        while authenticated users can perform any request.

        Parameters
        ----------
        request : rest_framework.request.Request
            The request object.
        view : rest_framework.views.APIView
            The view that the request is being made to.

        Returns
        -------
        bool
            True if the request has permission to access the view,
            False otherwise.
        """
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        """
        Determines if the request has permission to access a specific object.

        This method checks if the user is the author of the recipe or if the
        request method is a safe method (GET, HEAD, OPTIONS). Only the author
        of a recipe or users performing safe methods
        can access or modify the recipe.

        Parameters
        ----------
        request : rest_framework.request.Request
            The request object.
        view : rest_framework.views.APIView
            The view that the request is being made to.
        obj : Any
            The object the request is being made to.

        Returns
        -------
        bool
            True if the request has permission to access the object,
            False otherwise.
        """
        return (
            obj.author == request.user
            or request.method in permissions.SAFE_METHODS
        )
