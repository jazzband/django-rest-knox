import copy

from django.conf.urls import url
from django.conf.urls import include

from rest_framework import permissions
from rest_framework import serializers as drf_serializers
from rest_framework import viewsets
from rest_framework import routers
from rest_framework import decorators
from rest_framework import fields

from rest_auth import serializers
from rest_auth import views

from . import models
from . import forms


class PasswordChangeSerializer(serializers.PasswordChangeSerializer):
    """
    Use the password change form that re-encrypts all tokens.
    """

    set_password_form_class = forms.PasswordChangeForm


class PasswordChangeView(views.PasswordChangeView):
    """
    Use the password change form that re-encrypts all tokens.
    """

    serializer_class = PasswordChangeSerializer


class PasswordResetConfirmSerializer(
        serializers.PasswordResetConfirmSerializer):
    """
    Use the password reset form that deletes all tokens.
    """

    set_password_form_class = forms.SetPasswordForm


class PasswordResetConfirmView(views.PasswordResetConfirmView):
    """
    Use the password reset form that deletes all tokens.
    """

    serializer_class = PasswordResetConfirmSerializer


class NonEmptyLoginSerializer(serializers.LoginSerializer):
    """
    Don't allow empty login credentials.
    """

    def validate_empty_values(self, data):
        """
        Don't allow empty login credentials.
        """
        try:
            return super(
                NonEmptyLoginSerializer, self).validate_empty_values(data)
        except fields.SkipField:
            self.fail('required')


class AuthTokenModelSerializer(drf_serializers.ModelSerializer):
    """
    List, create, delete, or re-encrypt tokens.

    Requires the user's credentials.
    """

    login = NonEmptyLoginSerializer(required=True, write_only=True)
    token = drf_serializers.SerializerMethodField()

    class Meta:
        model = models.AuthToken
        fields = ('login', 'token', 'created', 'expires')

    def get_token(self, instance):
        """
        Decrypt the token using the password.
        """
        password = self.fields['login'].get_value(
            self.context['request'].data)['password']
        if password:
            return instance.decrypt(password)

    def create(self, validated_data):
        """
        Remove login credentials and pass in the user and password.
        """
        login = validated_data.pop('login')
        validated_data.update(
            user=self.context['request'].user, password=login['password'],
            return_instance=True)
        token = super(AuthTokenModelSerializer, self).create(validated_data)
        return token


class AuthTokenModelViewset(viewsets.ModelViewSet):
    """
    Abuse HTTP methods/verbs to support accepting creds as a request body.
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = AuthTokenModelSerializer
    queryset = models.AuthToken.objects.all()

    def get_queryset(self):
        """
        Operate on the authenticated user's tokens.
        """
        return super(AuthTokenModelViewset, self).get_queryset().filter(
            user=self.request.user)

    @decorators.list_route(methods=['post'])
    def list(self, request, *args, **kwargs):
        """
        Validate login credentials before delegating to the list method.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return super(AuthTokenModelViewset, self).list(
            request, *args, **kwargs)

    @decorators.detail_route(methods=['post'])
    def retrieve(self, request, *args, **kwargs):
        """
        Validate login credentials before delegating to the retrieve method.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return super(AuthTokenModelViewset, self).retrieve(
            request, *args, **kwargs)

    @decorators.detail_route(methods=['post'])
    def destroy(self, request, *args, **kwargs):
        """
        Validate login credentials before delegating to the destroy method.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return super(AuthTokenModelViewset, self).destroy(
            request, *args, **kwargs)


class EntityBodyRouter(routers.DefaultRouter):
    """
    The default router without for HTTP methods that ignore entity bodies.
    """

    # Deep copy of the default routes so we can modify the mappings
    # without changing the default routes.
    routes = copy.deepcopy(routers.DefaultRouter.routes)
    for route in routes:
        if isinstance(route, routers.Route):
            # Remove default routes for HTTP methods for which entity bodies
            # may be ignored and thus may be stripped by various proxies.
            route.mapping.pop('get', None)
            route.mapping.pop('delete', None)


body_router = EntityBodyRouter()
body_router.register(r'tokens', AuthTokenModelViewset)

urlpatterns = [
    url(r'^password/reset/confirm/$', PasswordResetConfirmView.as_view(),
        name='rest_password_reset_confirm'),
    url(r'^password/change/$', PasswordChangeView.as_view(),
        name='rest_password_change'),

    url(r'^', include(body_router.urls)),
]
