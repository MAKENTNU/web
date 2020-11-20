# Generated by Django 3.1.2 on 2020-11-20 13:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('groups', '0005_remove_committee_clickbait_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='committee',
            name='group',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='committee', to='groups.inheritancegroup', verbose_name='group'),
        ),
        migrations.AlterField(
            model_name='inheritancegroup',
            name='own_permissions',
            field=models.ManyToManyField(blank=True, related_name='inheritance_groups', to='auth.Permission'),
        ),
    ]
