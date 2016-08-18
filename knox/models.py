from django.conf import settings
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(self, user, expires=knox_settings.TOKEN_TTL):
        token = crypto.create_token_string()
        salt = crypto.create_salt_string()
        digest = crypto.hash_token(token, salt)

        if expires is not None:
            expires = timezone.now() + expires

        super(AuthTokenManager, self).create(
            token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH], digest=digest,
            salt=salt, user=user, expires=expires)
        # Note only the token - not the AuthToken object - is returned
        return token


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(
        max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True,
        null=True, blank=True)
    salt = models.CharField(
        max_length=CONSTANTS.SALT_LENGTH, unique=True)
    user = models.ForeignKey(
        User, null=False, blank=False, related_name='auth_token_set')
    created = models.DateTimeField(auto_now_add=True)
    expires = models. DateTimeField(null=True, blank=True)

    def __str__(self):
        return '%s : %s' % (self.digest, self.user)
