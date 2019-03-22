# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    replaces = [
        ('knox', '0005_authtoken_name'),
    ]

    dependencies = [
        ('knox', '0006_auto_20160818_0932'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='name',
            field=models.CharField(default=b'', max_length=200),
            preserve_default=True,
        ),
    ]
