# Generated by Django 4.0.6 on 2022-08-31 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0022_member_user_set_null_on_delete'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='gmail',
            new_name='google_email',
        ),
        migrations.AlterField(
            model_name='member',
            name='google_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Google email'),
        ),
    ]
