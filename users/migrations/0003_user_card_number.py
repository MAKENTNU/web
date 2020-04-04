# Generated by Django 2.2.5 on 2019-10-18 17:41

import card.models
import django.core.validators
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_rename_user_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='card_number',
            field=card.models.CardNumberField(error_messages={'unique': 'Card number already in use'}, max_length=10,
                                              null=True, unique=True, validators=[
                    django.core.validators.RegexValidator('^\\d{10}$', 'Card number must be ten digits long.')],
                                              verbose_name='Card number'),
        ),
    ]
