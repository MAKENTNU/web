# Generated by Django 2.2.5 on 2019-10-17 19:05

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False  # Required for sqlite<3.26
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
        migrations.AlterModelTable(
            name='user',
            table=None,
        ),
    ]
