from django.conf.urls import url

from rest_auth import serializers
from rest_auth import views

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


urlpatterns = [
    url(r'^password/reset/confirm/$', PasswordResetConfirmView.as_view(),
        name='rest_password_reset_confirm'),
    url(r'^password/change/$', PasswordChangeView.as_view(),
        name='rest_password_change'),
]
