from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

# Create your models here.
class EmailConfirmation(models.Model):
    account = models.OneToOneField(User, null=False, blank=False, related_name="email_confirmation")
    verified = models.BooleanField(null=False, blank=True, default=False)
