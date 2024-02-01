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
        self, user, expiry=knox_settings.TOKEN_TTL, prefix=knox_settings.TOKEN_PREFIX
    ):
        token = prefix + crypto.create_token_string()
        digest = crypto.hash_token(token)
        if expiry is not None:
            expiry = timezone.now() + expiry
        instance = super(AuthTokenManager, self).create(
            token_key=token[: CONSTANTS.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            expiry=expiry,
        )
        return instance, token


class AbstractAuthToken(models.Model):
    objects = AuthTokenManager()

    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH + CONSTANTS.TOKEN_KEY_LENGTH,
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="auth_token_set",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.digest} : {self.user}"


class AuthRefreshTokenManager(models.Manager):
    def create(self, user, expiry=knox_settings.REFRESH_TOKEN_TTL):
        token = crypto.create_token_string()
        digest = crypto.hash_token(token)

        if expiry is not None:
            expiry = timezone.now() + expiry

        instance = super(AuthRefreshTokenManager, self).create(
            token_key=token[: CONSTANTS.TOKEN_KEY_LENGTH],
            digest=digest,
            user=user,
            expiry=expiry,
        )
        return instance, token


class AbstractAuthRefreshToken(models.Model):
    objects = AuthRefreshTokenManager()

    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    token_key = models.CharField(
        max_length=CONSTANTS.MAXIMUM_TOKEN_PREFIX_LENGTH + CONSTANTS.TOKEN_KEY_LENGTH,
        db_index=True,
    )
    # auth_token = models.ForeignKey(AbstractAuthToken, on_delete=models.CASCADE, to_field='token_key')
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="refresh_token_set",
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "%s : %s" % (self.digest, self.user)


class RefreshFamilyManager(models.Manager):
    def create(self, user, token, refresh_token, parent=None):
        instance = super(RefreshFamilyManager, self).create(
            token=token[: CONSTANTS.TOKEN_KEY_LENGTH],
            parent=parent[: CONSTANTS.TOKEN_KEY_LENGTH]
            if parent
            else refresh_token[: CONSTANTS.TOKEN_KEY_LENGTH],
            refresh_token=refresh_token[: CONSTANTS.TOKEN_KEY_LENGTH],
            user=user,
        )
        return instance, token


class AbstractRefreshFamily(models.Model):
    objects = RefreshFamilyManager()
    parent = models.CharField(max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True)
    token = models.CharField(max_length=CONSTANTS.TOKEN_KEY_LENGTH, db_index=True)
    refresh_token = models.CharField(
        max_length=CONSTANTS.TOKEN_KEY_LENGTH, primary_key=True, db_index=True
    )
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        related_name="refresh_family_set",
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return "%s : %s" % (self.refresh_token[:5], self.user)


class AuthToken(AbstractAuthToken):
    class Meta:
        swappable = "KNOX_TOKEN_MODEL"


class AuthRefreshToken(AbstractAuthRefreshToken):
    class Meta:
        swappable = "KNOX_REFRESH_TOKEN_MODEL"


class RefreshFamily(AbstractRefreshFamily):
    class Meta:
        swappable = "KNOX_REFRESH_FAMILY_MODEL"


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


def get_refresh_token_model():
    """
    Return the AuthRefreshToken model that is active in this project.
    """

    try:
        return apps.get_model(knox_settings.REFRESH_TOKEN_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "REFRESH_TOKEN_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "REFRESH_TOKEN_MODEL refers to model '%s' that has not been installed"
            % knox_settings.REFRESH_TOKEN_MODEL
        )


def get_refresh_family_model():
    """
    Return the RefreshFamily model that is active in this project.
    """
    try:
        return apps.get_model(knox_settings.REFRESH_FAMILY_MODEL, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured(
            "REFRESH_FAMILY_MODEL must be of the form 'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "REFRESH_TOKEN_MODEL refers to model '%s' that has not been installed"
            % knox_settings.REFRESH_FAMILY_MODEL
        )
