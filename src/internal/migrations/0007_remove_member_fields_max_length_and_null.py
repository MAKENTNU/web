# Generated by Django 3.1.2 on 2020-10-22 22:36

from django.db import migrations, models
import phonenumber_field.modelfields
import web.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0006_secret'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='comment',
            field=models.TextField(blank=True, verbose_name='comment'),
        ),
        migrations.AlterField(
            model_name='member',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='contact email'),
        ),
        migrations.AlterField(
            model_name='member',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=32, region=None, verbose_name='phone number'),
        ),
        migrations.AlterField(
            model_name='member',
            name='reason_quit',
            field=models.TextField(blank=True, verbose_name='reason quit'),
        ),
        migrations.AlterField(
            model_name='member',
            name='role',
            field=web.modelfields.UnlimitedCharField(blank=True, verbose_name='role'),
        ),
        migrations.AlterField(
            model_name='member',
            name='study_program',
            field=web.modelfields.UnlimitedCharField(blank=True, verbose_name='study program'),
        ),
    ]
