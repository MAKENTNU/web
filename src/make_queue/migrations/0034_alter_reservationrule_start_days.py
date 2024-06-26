# Generated by Django 5.0.2 on 2024-04-04 17:18

import web.modelfields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0033_historicalmachine'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservationrule',
            name='start_days',
            field=web.modelfields.MultiSelectField(choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')], max_length=13, verbose_name='start days for rule periods'),
        ),
    ]
