# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0020_authtoken_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='is_system',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
