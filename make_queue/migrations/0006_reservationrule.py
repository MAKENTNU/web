# Generated by Django 2.1 on 2018-09-11 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0005_auto_20180425_1937'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReservationRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField(verbose_name='start time')),
                ('end_time', models.TimeField(verbose_name='end time')),
                ('days_changed', models.IntegerField(verbose_name='days')),
                ('start_days', models.IntegerField(default=0, verbose_name='start days for rule periods')),
                ('max_hours', models.FloatField(verbose_name='hours inside')),
                ('max_inside_border_crossed', models.FloatField(verbose_name='hours across borders')),
                ('machine_type', models.CharField(choices=[('3D-printer', '3D-printer'), ('Symaskin', 'Symaskin')], max_length=30, verbose_name='machine type')),
            ],
        ),
    ]
