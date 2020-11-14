# Generated by Django 3.1.2 on 2020-10-22 22:36

from django.db import migrations, models
import phonenumber_field.modelfields
import web.fields


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0005_remove_member_card_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Comment'),
        ),
        migrations.AlterField(
            model_name='member',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Contact email'),
        ),
        migrations.AlterField(
            model_name='member',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=32, region=None, verbose_name='Phone number'),
        ),
        migrations.AlterField(
            model_name='member',
            name='reason_quit',
            field=models.TextField(blank=True, verbose_name='Reason quit'),
        ),
        migrations.AlterField(
            model_name='member',
            name='role',
            field=web.fields.UnlimitedCharField(blank=True, verbose_name='Role'),
        ),
        migrations.AlterField(
            model_name='member',
            name='study_program',
            field=web.fields.UnlimitedCharField(blank=True, verbose_name='Study program'),
        ),
    ]