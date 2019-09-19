# Generated by Django 2.1.1 on 2018-10-04 16:07

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ToolsBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('image', models.ImageField(blank=True, upload_to='', verbose_name='Image')),
                ('content', ckeditor.fields.RichTextField()),
            ],
        ),
    ]