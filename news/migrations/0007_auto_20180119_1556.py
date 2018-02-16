# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-19 15:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import news.models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0006_auto_20180119_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='pub_time',
            field=models.TimeField(blank=True, default=news.models.time_now, null=True, verbose_name='Publiseringstid'),
        ),
        migrations.AlterField(
            model_name='article',
            name='pub_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Publiseringsdato'),
        ),
    ]
