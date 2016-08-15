# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def compute_time_from_expires(apps, schema_editor):
    AuthToken = apps.get_model("knox", "AuthToken")
    for authtoken in AuthToken.objects.all():
        authtoken.time = authtoken.expires - authtoken.created
        authtoken.save()


def compute_expires_from_time(apps, schema_editor):
    AuthToken = apps.get_model("knox", "AuthToken")
    for authtoken in AuthToken.objects.all():
        authtoken.expires = authtoken.created + authtoken.time
        authtoken.save()


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0004_authtoken_expires'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='time',
            field=models.DurationField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='authtoken',
            name='use',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(compute_time_from_expires, compute_expires_from_time),
        migrations.RemoveField(
            model_name='authtoken',
            name='expires',
        ),
    ]
