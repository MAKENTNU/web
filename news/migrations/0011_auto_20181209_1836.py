# Generated by Django 2.1.2 on 2018-12-09 17:36

from django.db import migrations
import web.multilingual.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0010_auto_20181013_1418'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsbase',
            name='clickbait',
            field=web.multilingual.modelfields.MultiLingualTextField(blank=True, max_length=300, verbose_name='Clickbait'),
        ),
        migrations.AlterField(
            model_name='newsbase',
            name='content',
            field=web.multilingual.modelfields.MultiLingualRichTextUploadingField(),
        ),
        migrations.AlterField(
            model_name='newsbase',
            name='title',
            field=web.multilingual.modelfields.MultiLingualTextField(max_length=100, verbose_name='Title'),
        ),
    ]
