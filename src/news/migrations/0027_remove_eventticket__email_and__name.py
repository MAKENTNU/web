# Generated by Django 3.2.11 on 2022-03-14 03:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_tickets_without_user(apps, schema_editor):
    EventTicket = apps.get_model('news', 'EventTicket')
    EventTicket.objects.filter(user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0026_alter_article_and_event_image_filename'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventticket',
            name='_email',
        ),
        migrations.RemoveField(
            model_name='eventticket',
            name='_name',
        ),
        migrations.RunPython(delete_tickets_without_user, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='eventticket',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_tickets', to='users.user', verbose_name='user'),
        ),
    ]
