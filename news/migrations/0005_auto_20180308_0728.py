# Generated by Django 2.0.1 on 2018-03-08 06:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_auto_20180307_1352'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='newsbase',
            options={'permissions': (('can_view_private', 'Can view private news'),)},
        ),
    ]
