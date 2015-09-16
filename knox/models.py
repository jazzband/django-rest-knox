from django.conf import settings
from django.db import models

from knox.settings import CONSTANTS

User = settings.AUTH_USER_MODEL

class AuthToken(models.Model):


    digest = models.CharField(max_length=CONSTANTS.DIGEST_LENGTH, primary_key=True)
    salt = models.CharField(max_length=CONSTANTS.SALT_LENGTH, unique=True)
    user = models.ForeignKey(User, null=False, blank=False, related_name="auth_token_set")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s : %s" % (self.key, self.user)
