from django.conf import settings
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(self, user, expiry=knox_settings.TOKEN_TTL):
        crypto_obj = self.generate_token()
        token = crypto_obj.get("token")
        digest = crypto_obj.get("digest")
        expiry = crypto_obj.get("expiry")
        instance = super(AuthTokenManager, self).create(
            token_key=token[: CONSTANTS.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            expiry=expiry,
        )
        return instance, token

    def generate_token(self):
        """
        Returns a dict with token, digest and expiry datetime

        Example:
        {
          "token": <token string>,
          "expiry": <digest hash>,
          "expiry": <expiry datetime>,
        }
        """
        token = crypto.create_token_string()
        digest = crypto.hash_token(token)

        if expiry is not None:
            expiry = timezone.now() + expiry
        return {"token": token, "digest": digest, "expiry": expiry}


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True)
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="auth_token_set",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "%s : %s" % (self.digest, self.user)
