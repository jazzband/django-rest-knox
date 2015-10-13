# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0003_auto_20150916_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='authtoken',
            name='expires',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
