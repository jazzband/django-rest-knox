# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0002_auto_20150916_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authtoken',
            name='digest',
            field=models.CharField(primary_key=True, serialize=False, max_length=128),
        ),
        migrations.AlterField(
            model_name='authtoken',
            name='salt',
            field=models.CharField(unique=True, max_length=16),
        ),
    ]
