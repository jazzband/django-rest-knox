import datetime

from cryptography.fernet import Fernet

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils import encoding

from knox import crypto
from knox.settings import CONSTANTS, knox_settings

User = settings.AUTH_USER_MODEL

class AuthTokenManager(models.Manager):
    def create(
            self, user, password=None, expires=knox_settings.TOKEN_TTL,
            return_instance=False):
        token = crypto.create_token_string()
        salt = crypto.create_salt_string()
        digest = crypto.hash_token(token, salt)

        encrypted = None
        if password:
            fernet = Fernet(crypto.derive_fernet_key(password, salt))
            encrypted = fernet.encrypt(encoding.force_bytes(token))

        if expires is not None:
             expires = timezone.now() + expires

        auth_token = super(AuthTokenManager, self).create(
            digest=digest, salt=salt, encrypted=encrypted,
            user=user, expires=expires)
        if return_instance:
            return auth_token
        return token # Note only the token - not the AuthToken object - is returned

    def change_passwords(self, user, old_password, new_password):
        """
        Re-encrypt all of a user's tokens given a new password.
        """
        tokens = self.filter(user=user, encrypted__isnull=False)
        count = tokens.count()
        for token_obj in tokens:
            token_obj.change_password(old_password, new_password)
        return count

    def reset_passwords(self, user):
        """
        Delete all a user's encrypted tokens on passwors reset
        """
        tokens = self.filter(user=user, encrypted__isnull=False)
        return tokens.delete()


class AuthToken(models.Model):

    objects = AuthTokenManager()

    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    encrypted = models.CharField(
        max_length=CONSTANTS.ENCRYPTED_LENGTH, null=True)
    salt = models.CharField(max_length=CONSTANTS.SALT_LENGTH, unique=True)
    user = models.ForeignKey(User, null=False, blank=False, related_name="auth_token_set")
    created = models.DateTimeField(auto_now_add=True)
    expires = models. DateTimeField(null=True, blank=True)

    def __str__(self):
        return "%s : %s" % (self.digest, self.user)

    def decrypt(self, password):
        """
        Return the plain text token after decrypting it using the password.
        """
        fernet = Fernet(crypto.derive_fernet_key(password, self.salt))
        return fernet.decrypt(encoding.force_bytes(self.encrypted))

    def change_password(self, old_password, new_password):
        """
        Re-encrypt the token given the current password and a new password.
        """
        token = self.decrypt(old_password)
        fernet = Fernet(crypto.derive_fernet_key(new_password, self.salt))
        self.encrypted = fernet.encrypt(encoding.force_bytes(token))
        self.save()
        return self.encrypted
