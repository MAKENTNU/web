# Generated by Django 2.1.2 on 2018-11-03 14:24

import ckeditor_uploader.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import make_queue.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('make_queue', '0007_auto_20180914_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineUsageRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('machine_type', models.IntegerField(choices=[(1, '3D-printers'), (2, 'Sewing machines')], unique=True)),
                ('content', ckeditor_uploader.fields.RichTextUploadingField()),
                ('content_en', ckeditor_uploader.fields.RichTextUploadingField()),
            ],
        ),
        migrations.CreateModel(
            name='Printer3DCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', make_queue.models.fields.UsernameField(max_length=32, verbose_name='username')),
                ('date', models.DateField(verbose_name='course date')),
                ('card_number', models.IntegerField(null=True, verbose_name='card number (EM)')),
                ('name', models.CharField(max_length=256, verbose_name='full name')),
                ('status', models.CharField(choices=[('registered', 'Registered'), ('sent', 'Sent to Building security'), ('access', 'Access granted')], default='registered', max_length=20, verbose_name='status')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
        migrations.AlterField(
            model_name='quota',
            name='all',
            field=models.BooleanField(default=False, verbose_name='all users'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='diminishing',
            field=models.BooleanField(default=False, verbose_name='diminishing'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='ignore_rules',
            field=models.BooleanField(default=False, verbose_name='ignores rules'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='machine_type',
            field=models.IntegerField(choices=[(1, '3D-printers'), (2, 'Sewing machines')], null=True, verbose_name='machine type'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='number_of_reservations',
            field=models.IntegerField(default=3, verbose_name='number of reservations'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='special_text',
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name='reservationrule',
            name='machine_type',
            field=models.IntegerField(choices=[(1, '3D-printers'), (2, 'Sewing machines')], verbose_name='machine type'),
        ),
    ]