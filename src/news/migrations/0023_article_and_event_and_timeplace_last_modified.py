# Generated by Django 3.2.8 on 2021-11-01 11:10

from datetime import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0022_abstract_newsbase'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, default=datetime.utcfromtimestamp(0).replace(tzinfo=utc), verbose_name='last modified'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='event',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, default=datetime.utcfromtimestamp(0).replace(tzinfo=utc), verbose_name='last modified'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='timeplace',
            name='last_modified',
            field=models.DateTimeField(auto_now=True, default=datetime.utcfromtimestamp(0).replace(tzinfo=utc), verbose_name='last modified'),
            preserve_default=False,
        ),
    ]