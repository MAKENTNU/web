# Generated by Django 4.0.4 on 2022-05-20 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('makerspace', '0008_alter_equipment_image_filename'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='equipment',
            options={'verbose_name': 'equipment', 'verbose_name_plural': 'equipment'},
        ),
        migrations.AlterModelOptions(
            name='historicalequipment',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical equipment', 'verbose_name_plural': 'historical equipment'},
        ),
        migrations.AlterField(
            model_name='historicalequipment',
            name='history_date',
            field=models.DateTimeField(db_index=True),
        ),
    ]
