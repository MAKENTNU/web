# Generated by Django 3.1.4 on 2020-12-15 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0010_add_related_names'),
    ]

    operations = [
        migrations.AddField(
            model_name='secret',
            name='priority',
            field=models.IntegerField(blank=True, help_text='If specified, the secrets are sorted ascending by this value.', null=True, verbose_name='priority'),
        ),
    ]
