# Generated by Django 2.0.1 on 2018-05-01 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0007_auto_20180412_1740'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='multiday',
            field=models.BooleanField(default=False, verbose_name='single registration'),
        ),
    ]
