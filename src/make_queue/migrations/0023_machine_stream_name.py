# Generated by Django 3.0.10 on 2020-11-09 23:55

import django.core.validators
from django.db import migrations, models
from django.utils.text import slugify
import re


def set_stream_name(apps, schema_editor):
    Machine = apps.get_model('make_queue', 'Machine')
    db_alias = schema_editor.connection.alias

    for machine in Machine.objects.using(db_alias).filter(machine_type__has_stream=True):
        # Roughly makes the name lowercase, and replaces spaces with hyphens, and special characters with their ASCII equivalent (like ö -> o)
        machine.stream_name = slugify(machine.name)
        machine.save()


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0022_printer3dcourse_user_onetoone_and_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='machine',
            name='stream_name',
            field=models.CharField(blank=True, default='', help_text="Used for connecting to the machine's stream.", max_length=50, validators=[django.core.validators.RegexValidator(code='invalid_lowercase_slug', message='This can only consist of lowercase English letters, numbers, hyphens or underscores.', regex=re.compile('^[a-z0-9_-]+$'))], verbose_name='stream name'),
        ),
        migrations.RunPython(set_stream_name, migrations.RunPython.noop),
    ]
