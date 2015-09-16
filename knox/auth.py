from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import authentication

from knox.crypto import hash_token
from knox.models import AuthToken

User = settings.AUTH_USER_MODEL

class TokenAuthentication(authentication.TokenAuthentication):
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
