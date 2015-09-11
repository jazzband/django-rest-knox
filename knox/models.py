from django.conf import settings
from django.db import models

import binascii
import OpenSSL

User = settings.AUTH_USER_MODEL

# Create your models here.
class EmailConfirmation(models.Model):
    account = models.OneToOneField(User, null=False, blank=False, related_name="email_confirmation")
    verified = models.BooleanField(null=False, blank=True, default=False)

    def __str__(self):
        return "%s: %s" % (self.account, ("email verified" if self.verified else "email not verified"))

class AuthToken(models.Model):

    KEY_LENGTH = 64;

    key = models.CharField(max_length=KEY_LENGTH, primary_key=True)
    user = models.ForeignKey(User, null=False, blank=False, related_name="auth_token_set")
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        else:
            return # Do not allow editing of generated keys
        return super().save(*args, **kwargs)

    @staticmethod
    def generate_key():
        return binascii.hexlify(OpenSSL.rand.bytes(int(AuthToken.KEY_LENGTH / 2))).decode()

    def __str__(self):
        return "%s : %s" % (self.key, self.user)
