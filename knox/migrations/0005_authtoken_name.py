# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0004_authtoken_expires'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='name',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
    ]
