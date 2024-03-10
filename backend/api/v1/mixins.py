# DRF Library
from rest_framework.mixins import UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response


class PatchNotPutModelMixin(UpdateModelMixin):
    """
    A mixin to override the default behavior
    of the update method to use partial_update instead.

    This mixin is useful when you want to use PATCH requests
    for partial updates instead of PUT,
    which is the default behavior in Django Rest Framework.
    """

    def partial_update(
            self,
            request: Request,
            *args: tuple,
            **kwargs: dict,
    ) -> Response:
        """
        Handles partial updates of a model instance.

        This method is overridden to use the partial_update method
        from the UpdateModelMixin,
        effectively treating PATCH requests as if they were PUT requests.

        Parameters
        ----------
        request : rest_framework.request.Request
            The request object.
        *args : tuple
            Positional arguments.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        rest_framework.response.Response
            The response object.

        Raises
        ------
        NotImplementedError
            If the partial_update method is not implemented in the superclass.
        """
        return super().update(request, *args, **kwargs)
