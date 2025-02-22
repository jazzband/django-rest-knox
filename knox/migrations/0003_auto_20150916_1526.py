# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def populate_salt_field_with_dummy_data(apps, schema_editor):
    """we just populate salt field with index to make it unique"""

    AuthToken = apps.get_model("knox", "AuthToken")
    for index, token in enumerate(AuthToken.objects.all()):
        token.salt = index
        token.save(update_fields=["salt"])


def delete_all_rows(apps, schema_editor):
    """Since digest field is the pk best way to revert migrations is just to delete all Auth token rows"""

    AuthToken = apps.get_model("knox", "AuthToken")
    AuthToken.objects.using(schema_editor.connection.alias).all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('knox', '0002_auto_20150916_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name="authtoken",
            name="digest",
            field=models.CharField(primary_key=True, serialize=False, max_length=128),
        ),
        migrations.RunPython(migrations.RunPython.noop, delete_all_rows),
        migrations.AlterField(
            model_name="authtoken",
            name="salt",
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.RunPython(
            migrations.RunPython.noop, populate_salt_field_with_dummy_data
        ),
    ]
