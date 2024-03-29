# Generated by Django 4.0.4 on 2022-05-20 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0028_add_eventticket_constraints'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalarticle',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical article', 'verbose_name_plural': 'historical articles'},
        ),
        migrations.AlterModelOptions(
            name='historicalevent',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical event', 'verbose_name_plural': 'historical events'},
        ),
        migrations.AlterField(
            model_name='historicalarticle',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalevent',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]
