# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models

knox_settings = getattr(settings, 'KNOX_SETTING', {})
token_model = knox_settings.get('TOKEN_MODEL', 'knox.AuthToken')


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(token_model),
    ]
    operations = [
        migrations.CreateModel(
            name="AuthToken",
            fields=[
                (
                    "key",
                    models.CharField(max_length=64, serialize=False, primary_key=True),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        related_name="auth_token_set",
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
    ]
