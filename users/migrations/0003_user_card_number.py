# Generated by Django 2.2.5 on 2019-10-18 17:41

import card.models
import django.core.validators
from django.db import migrations


def card_number(apps, schema_editor):
    Course = apps.get_model('make_queue', 'Printer3DCourse')
    db_alias = schema_editor.connection.alias

    for course in Course.objects.using(db_alias).filter(user__isnull=False, _card_number__isnull=False):
        course.user.card_number = course._card_number
        course.user.save(using=db_alias)
        course._card_number = None
        course.save(using=db_alias)


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_rename_user_table'),
        ('make_queue', '0013_course_card_number_field'),
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
        migrations.RunPython(card_number, migrations.RunPython.noop),
    ]