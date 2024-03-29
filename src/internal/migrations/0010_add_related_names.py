# Generated by Django 3.1.2 on 2020-11-20 13:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0004_auto_20181009_1356'),
        ('internal', '0009_alter_id_fields_to_use_bigautofield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='committees',
            field=models.ManyToManyField(blank=True, related_name='members', to='groups.Committee', verbose_name='committees'),
        ),
        migrations.AlterField(
            model_name='member',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='member', to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='systemaccess',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='system_accesses', to='internal.member', verbose_name='member'),
        ),
    ]
