# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel('AuthToken'),
        migrations.CreateModel(
        name='AuthToken',
        fields=[
            ('digest', models.CharField(max_length=64, serialize=False, primary_key=True)),
            ('salt', models.CharField(max_length=16, serialize=False, unique=True)),
            ('created', models.DateTimeField(auto_now_add=True)),
            ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='auth_token_set', on_delete=models.CASCADE)),
        ],)
    ]
