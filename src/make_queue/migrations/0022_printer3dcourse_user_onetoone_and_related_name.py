# Generated by Django 3.1.2 on 2020-11-20 13:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('make_queue', '0021_alter_id_fields_to_use_bigautofield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printer3dcourse',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='printer_3d_course', to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
