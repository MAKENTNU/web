# Generated by Django 2.2.5 on 2019-10-23 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('makerspace', '0005_tools'),
    ]

    operations = [
        migrations.CreateModel(
            name='Musician',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('instrument', models.CharField(max_length=100)),
            ],
        ),
    ]