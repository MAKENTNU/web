# Generated by Django 3.0.4 on 2020-03-14 10:09

import datetime
from django.db import migrations, models
import web.multilingual.database


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='content',
            field=web.multilingual.database.MultiLingualTextField(max_length=256, verbose_name='Content'),
        ),
        migrations.AlterField(
            model_name='announcement',
            name='display_from',
            field=models.DateTimeField(default=datetime.datetime(2020, 3, 14, 11, 9, 17, 414974)),
        ),
    ]
