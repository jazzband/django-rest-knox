from typing import Any

from django import forms
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from knox import models
from knox.settings import CONSTANTS


class AuthTokenCreateForm(forms.ModelForm):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(AuthTokenCreateForm, self).__init__(*args, **kwargs)
        self.token: str | None = None

    class Meta:
        model = models.AuthToken
        fields = ['user', 'expiry']

    def save(self, commit: bool = True) -> models.AuthToken:
        obj = super(AuthTokenCreateForm, self).save(commit=False)
        digest, token = models.get_digest_token()
        obj.digest = digest
        obj.token_key = token[:CONSTANTS.TOKEN_KEY_LENGTH]
        self.token = token
        if commit:
            obj.save()
            obj.save_m2m()
        return obj


@admin.register(models.AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    add_form = AuthTokenCreateForm
    list_display = ('digest', 'user', 'created', 'expiry',)
    # We dont know how a custom User model looks like, but is must have a USERNAME_FIELD
    search_fields = ['digest', 'token_key', 'user__'+get_user_model().USERNAME_FIELD]
    fields = ()
    raw_id_fields = ('user',)

    def get_form(
        self, request: HttpRequest, obj: models.AuthToken | None = None, **kwargs: Any
    ) -> type[forms.ModelForm]:
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super(AuthTokenAdmin, self).get_form(request, obj, **defaults)

    def save_model(
        self,
        request: HttpRequest,
        obj: models.AuthToken,
        form: AuthTokenCreateForm,
        change: bool,
    ) -> None:
        if not change:
            self.message_user(request, "TOKEN " + form.token, messages.INFO)
        super(AuthTokenAdmin, self).save_model(request, obj, form, change)
