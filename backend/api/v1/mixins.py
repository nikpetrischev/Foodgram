# DRF Library
from rest_framework.mixins import UpdateModelMixin


class PatchNotPutModelMixin(UpdateModelMixin):
    def partial_update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
