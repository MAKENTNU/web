# Generated by Django 3.2.2 on 2021-05-11 15:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0004_remove_announcement_fields_max_length_and_null'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]