from http import HTTPStatus

from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import CustomUser, Subscriptions
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
    # http_method_names = ['get', 'post']

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

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        current_user = request.user
        subscriptions = Subscriptions.objects.filter(
            subscriber=current_user.id,
        )
        data = []
        for subscription in subscriptions:
            subs_user = CustomUser.objects.get(pk=subscription.id)
            data_dict = self.get_serializer(subs_user).data
            data.append(data_dict)

        return Response(data=data, status=HTTPStatus.OK)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        if request.user.id == id:
            return Response(
                data={'error':
                      f'Подписка на самого себя недопустима'},
                status=HTTPStatus.BAD_REQUEST,
            )
        subs_user = get_object_or_404(CustomUser, pk=id)
        _, created = Subscriptions.objects.get_or_create(
            subscriber=request.user,
            subscribe_to=subs_user,
        )
        if not created:
            return Response(
                data={'error':
                      f'Подписка на {subs_user.username} уже оформлена'},
                status=HTTPStatus.BAD_REQUEST,
            )
        return Response(
            data=self.get_serializer(subs_user).data,
            status=HTTPStatus.CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        subs_user = get_object_or_404(CustomUser, pk=id)
        try:
            subscription = Subscriptions.objects.get(
                subscriber=request.user.id,
                subscribe_to=subs_user.id,
            )
        except ObjectDoesNotExist as err:
            return Response(
                data={'error': str(err)},
                status=HTTPStatus.BAD_REQUEST,
            )
        subscription.delete()
        return Response(status=HTTPStatus.NO_CONTENT)
