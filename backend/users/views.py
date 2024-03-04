# Standart Library
# Standard Library
from http import HTTPStatus

# Django Library
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404

# DRF Library
from rest_framework import filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Local Imports
from .models import CustomUser, Subscriptions
from .serializers import ExpandedUserSerializer, UserSerializer


class UserModelViewSet(ModelViewSet):
    model = CustomUser
    queryset = CustomUser.objects.order_by('id')
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['=username']

    def get_serializer_class(self):
        if ('/subscriptions/' in self.request.path
                or '/subscribe/' in self.request.path):
            return ExpandedUserSerializer
        return UserSerializer

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        context['request'] = self.request
        kwargs.setdefault('context', context)
        return serializer_class(*args, **kwargs)

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
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        user = authenticate(
            username=request.user.username,
            password=current_password,
        )
        if user is not None:
            user.set_password(new_password)
            user.save()
            return Response(status=HTTPStatus.NO_CONTENT)
        return Response(
            data={'error': 'Wrong password'},
            status=HTTPStatus.BAD_REQUEST,
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        recipes_limit = request.query_params.get('recipes_limit')
        subscriptions = request.user.subscriptions.all()

        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={
                    'request': request,
                    'recipes_limit': recipes_limit,
                },
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            subscriptions,
            many=True,
            context={
                'request': request,
                'recipes_limit': recipes_limit,
            },
        )
        return Response(data=serializer.data, status=HTTPStatus.OK)

    @action(
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        if request.user.id == int(id):
            return Response(
                data={'error':
                      'Подписка на самого себя недопустима'},
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
        recipes_limit = request.query_params.get('recipes_limit')
        context = {
            'request': request,
            'recipes_limit': recipes_limit,
        }
        return Response(
            data=self.get_serializer(subs_user, context=context).data,
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
