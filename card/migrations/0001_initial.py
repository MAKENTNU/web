# Generated by Django 2.2.4 on 2019-09-22 17:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def course_registration_card(apps, schema_editor):
    """
    Create Card objects to connect course registration card_number to registration user
    """
    Card = apps.get_model('card', 'Card')
    Printer3DCourse = apps.get_model('make_queue', 'Printer3DCourse')
    db_alias = schema_editor.connection.alias

    for registration in Printer3DCourse.objects.using(db_alias).all():
        if hasattr(registration, 'user') and registration.user and registration.card_number:
            user = registration.user
            if not hasattr(user, 'card'):
                Card.objects.using(db_alias).create(user=user, number="EM " + str(registration.card_number).zfill(10))


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('make_queue', '0008_auto_20181103_1524'),  # Printer3DCourse model
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=16, verbose_name='Card number')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.AddConstraint(
            model_name='card',
            constraint=models.UniqueConstraint(fields=('number',), name='unique_number'),
        ),
        migrations.RunPython(course_registration_card, migrations.RunPython.noop)
    ]