try:
    from hmac import compare_digest
except ImportError:
    def compare_digest(a, b):
        return a == b

import binascii

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from rest_framework import exceptions
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header
)

from knox.crypto import hash_token
from knox.models import AuthToken
from knox.settings import CONSTANTS

User = settings.AUTH_USER_MODEL


class TokenAuthentication(BaseAuthentication):
    '''
    This authentication scheme uses Knox AuthTokens for authentication.

    Similar to DRF's TokenAuthentication, it overrides a large amount of that
    authentication scheme to cope with the fact that Tokens are not stored
    in plaintext in the database

    If succesful
    - `request.user` will be a django `User` instance
    - `request.auth` will be an `AuthToken` instance
    '''
    model = AuthToken

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'token':
            return None
        if len(auth) == 1:
            msg = _('Invalid token header. No credentials provided.')
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = _('Invalid token header. '
                    'Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        user, auth_token = self.authenticate_credentials(auth[1])
        return (user, auth_token)

    def authenticate_credentials(self, token):
        '''
        Due to the random nature of hashing a salted value, this must inspect
        each auth_token individually to find the correct one.

        Tokens that have expired will be deleted and skipped
        '''
        msg = _('Invalid token.')
        token = token.decode("utf-8")
        for auth_token in AuthToken.objects.filter(
                token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH]):
            for other_token in auth_token.user.auth_token_set.all():
                if other_token.digest != auth_token.digest and other_token.expires is not None:
                    if other_token.expires < timezone.now():
                        other_token.delete()
            if auth_token.expires is not None:
                if auth_token.expires < timezone.now():
                    auth_token.delete()
                    continue
            try:
                digest = hash_token(token, auth_token.salt)
            except (TypeError, binascii.Error):
                raise exceptions.AuthenticationFailed(msg)
            if compare_digest(digest, auth_token.digest):
                return self.validate_user(auth_token)
        # Authentication with this token has failed
        raise exceptions.AuthenticationFailed(msg)

    def validate_user(self, auth_token):
        if not auth_token.user.is_active:
            raise exceptions.AuthenticationFailed(
                _('User inactive or deleted.'))
        return (auth_token.user, auth_token)

    def authenticate_header(self, request):
        return 'Token'
