from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils import timezone

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

sha = knox_settings.SECURE_HASH_ALGORITHM

User = settings.AUTH_USER_MODEL


class AuthTokenManager(models.Manager):
    def create(
        self,
        user,
        expiry=knox_settings.TOKEN_TTL,
        prefix=knox_settings.TOKEN_PREFIX,
        **kwargs
    ):
        token = prefix + crypto.create_token_string()
        digest = crypto.hash_token(token)
        if expiry is not None:
            expiry = timezone.now() + expiry
        instance = super().create(
            token_key=token[:CONSTANTS.TOKEN_KEY_LENGTH], digest=digest,
            user=user, expiry=expiry, **kwargs)
        return instance, token


class AbstractAuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(
        max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH +
        CONSTANTS.TOKEN_KEY_LENGTH,
        db_index=True
    )
    user = models.ForeignKey(User, null=False, blank=False,
                             related_name='auth_token_set', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.digest} : {self.user}'


class AuthToken(AbstractAuthToken):
    class Meta:
        swappable = 'KNOX_TOKEN_MODEL'


def get_token_model():
    """
    Return the AuthToken model that is active in this project.
    """

    try:
        return apps.get_model(knox_settings.TOKEN_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "TOKEN_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "TOKEN_MODEL refers to model '%s' that has not been installed"
            % knox_settings.TOKEN_MODEL
        )
