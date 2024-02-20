from http import HTTPStatus

from rest_framework import permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import CustomUser
from .serializers import (
    UserSerializer,
    ChangePasswordSerializer,
)


class UserModelViewSet(ModelViewSet):
    model = CustomUser
    serializer_class = UserSerializer
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['=username']
    http_method_names = ['get', 'post']

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        context['request'] = self.request
        kwargs.setdefault('context', context)
        return serializer_class(*args, **kwargs)

    def get_queryset(self):
        # TODO: Add all related queries.
        queryset = CustomUser.objects.order_by('id')
        return queryset

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=['post'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_password(self, request):
        user: CustomUser = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            current_password = serializer.data.get('current_password')
            if current_password != user.password:
                return Response(
                    {'current_password': 'Wrong password'},
                    status=HTTPStatus.BAD_REQUEST,
                )
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response(status=HTTPStatus.NO_CONTENT)

        return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
