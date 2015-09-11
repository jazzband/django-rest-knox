from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import authentication

from knox.models import AuthToken

User = settings.AUTH_USER_MODEL

class TokenAuthentication(authentication.TokenAuthentication):
    '''
    This authentication scheme uses Knox AuthTokens for authentication.

    Similar to DRF's TokenAuthentication, but with longer keys and the possibility
    for multiple valid keys simultaneously (giving a session-like interface for
    RESTful applications)

    If succesful
    - `request.user` will be a django `User` instance
    - `request.auth` will be an `AuthToken` instance
    '''

    model = AuthToken
