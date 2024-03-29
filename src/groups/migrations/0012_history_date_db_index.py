# Generated by Django 4.0.4 on 2022-05-20 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0011_historicalinheritancegroup'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalcommittee',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical committee', 'verbose_name_plural': 'historical committees'},
        ),
        migrations.AlterModelOptions(
            name='historicalinheritancegroup',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical inheritance group', 'verbose_name_plural': 'historical inheritance groups'},
        ),
        migrations.AlterField(
            model_name='historicalcommittee',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalinheritancegroup',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]
