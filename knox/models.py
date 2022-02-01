from django.conf import settings
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(self, user, expiry=knox_settings.TOKEN_TTL):
        token = crypto.create_token_string()
        digest = crypto.hash_token(token)

        if expiry is not None:
            expiry = timezone.now() + expiry

        instance = super(AuthTokenManager, self).create(
            token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH], digest=digest,
            user=user, expiry=expiry)
        return instance, token


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(
        max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True)
    user = models.ForeignKey(User, null=False, blank=False,
                             related_name='auth_token_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s : %s' % (self.digest, self.user)


from types import SimpleNamespace
from knox.settings import CONSTANTS, knox_settings

def get_token_from_request_header(request):
    # here by default knox_settings.AUTH_HEADER_PREFIX is Token
    if "Authorization" in request.headers:
        try:
            _, token = request.headers["Authorization"].split(" ")
        except:
            return None
        if _ != knox_settings.AUTH_HEADER_PREFIX:
            return None
        return token

def get_user_from_token(token):
    objs = AuthToken.objects.filter(token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH])
    if len(objs) == 0:
        return None
    return objs.first().user

# a decorator to get user from valid request with token
def smart_token_user(func):
    def inner(clsf, request, *args, **kwargs):
        token = get_token_from_request_header(request=request)
        if token is not None:
            the_user = get_user_from_token(token)
            if the_user is not None:
                request.user = SimpleNamespace()
                request.user = the_user
                return func(clsf, request, *args, **kwargs)
    return inner