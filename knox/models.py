from django.conf import settings
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(self, user, expiry=knox_settings.TOKEN_TTL):
        token = crypto.create_token_string()
        salt = crypto.create_salt_string()
        digest = crypto.hash_token(token, salt)

        if expiry is not None:
            expiry = timezone.now() + expiry

        instance = super(AuthTokenManager, self).create(
            token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH], digest=digest,
            salt=salt, user=user, expiry=expiry)
        return instance, token


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(
        max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True)
    salt = models.CharField(
        max_length=CONSTANTS.SALT_LENGTH, unique=True)
    user = models.ForeignKey(User, null=False, blank=False,
                             related_name='auth_token_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s : %s' % (self.digest, self.user)
