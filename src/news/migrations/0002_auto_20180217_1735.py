# Generated by Django 2.0.1 on 2018-02-17 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='timeplace',
            options={'ordering': ('start_date',)},
        ),
        migrations.AddField(
            model_name='timeplace',
            name='hidden',
            field=models.BooleanField(default=True, verbose_name='skjult'),
        ),
    ]