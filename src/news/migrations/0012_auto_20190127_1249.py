# Generated by Django 2.1.5 on 2019-01-27 11:49

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0011_auto_20181209_1836'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventTicket',
            fields=[
                ('name', models.CharField(max_length=128, verbose_name='name')),
                ('email', models.EmailField(max_length=254, verbose_name='email')),
                ('active', models.BooleanField(default=True, verbose_name='active')),
                ('comment', models.TextField(blank=True, max_length=1000, verbose_name='comment')),
                ('language', models.CharField(choices=[('en', 'English'), ('nb', 'Norwegian')], default='en', max_length=2, verbose_name='preferred language')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ],
            options={
                'permissions': (('cancel_ticket', 'Can cancel and reactivate all event tickets'),),
            },
        ),
        migrations.AddField(
            model_name='event',
            name='number_of_tickets',
            field=models.IntegerField(default=0, verbose_name='number of available tickets'),
        ),
        migrations.AddField(
            model_name='timeplace',
            name='number_of_tickets',
            field=models.IntegerField(default=0, verbose_name='number of available tickets'),
        ),
        migrations.AlterField(
            model_name='timeplace',
            name='end_time',
            field=models.TimeField(default=datetime.time(0, 0), verbose_name='end time'),
        ),
        migrations.AddField(
            model_name='eventticket',
            name='event',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='news.Event', verbose_name='event'),
        ),
        migrations.AddField(
            model_name='eventticket',
            name='timeplace',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='news.TimePlace', verbose_name='timeplace'),
        ),
        migrations.AddField(
            model_name='eventticket',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='user'),
        ),
    ]
