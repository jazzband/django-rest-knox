from django.conf import settings
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings


User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(self, user, time=knox_settings.DEFAULT_TOKEN_TTL, use=knox_settings.DEFAULT_TOKEN_USE):
        token = crypto.create_token_string()
        salt = crypto.create_salt_string()
        digest = crypto.hash_token(token, salt)

        auth_token = super(AuthTokenManager, self).create(digest=digest, salt=salt, user=user, time=time, use=use)
        return token # Note only the token - not the AuthToken object - is returned


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    salt = models.CharField(max_length=CONSTANTS.SALT_LENGTH, unique=True)
    user = models.ForeignKey(User, null=False, blank=False, related_name="auth_token_set")
    created = models.DateTimeField(auto_now_add=True)
    time = models.DurationField(null=True, blank=True)
    use = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return "%s : %s" % (self.digest, self.user)

    def decrement(self):
        self.use -= 1
        self.save()
