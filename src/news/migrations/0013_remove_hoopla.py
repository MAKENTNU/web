# Generated by Django 2.1.5 on 2019-02-23 00:33

from django.db import migrations
import web.multilingual.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0012_auto_20190127_1249'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='hoopla',
        ),
        migrations.RemoveField(
            model_name='timeplace',
            name='hoopla',
        ),
        migrations.AlterField(
            model_name='newsbase',
            name='content',
            field=web.multilingual.modelfields.MultiLingualRichTextUploadingField(verbose_name='content'),
        ),
    ]
