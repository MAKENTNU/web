# Generated by Django 3.0.5 on 2020-09-05 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('makerspace', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Tool',
            new_name='Equipment',
        ),
        migrations.AlterField(
            model_name='equipment',
            name='image',
            field=models.ImageField(upload_to='equipment', verbose_name='Image'),
        ),
    ]
