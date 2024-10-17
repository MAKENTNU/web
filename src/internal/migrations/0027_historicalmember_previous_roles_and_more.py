# Generated by Django 5.0.2 on 2024-10-17 16:48

import web.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0026_add_secret_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalmember',
            name='previous_roles',
            field=web.modelfields.UnlimitedCharField(blank=True, verbose_name='previous roles'),
        ),
        migrations.AddField(
            model_name='member',
            name='previous_roles',
            field=web.modelfields.UnlimitedCharField(blank=True, verbose_name='previous roles'),
        ),
    ]
