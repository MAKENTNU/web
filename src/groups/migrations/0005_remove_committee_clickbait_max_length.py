# Generated by Django 3.1.2 on 2020-10-30 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_auto_20181009_1356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='committee',
            name='clickbait',
            field=models.TextField(blank=True, verbose_name='clickbait'),
        ),
    ]
