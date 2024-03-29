# Generated by Django 3.0.10 on 2020-11-12 15:25

from django.db import migrations, models
import web.multilingual.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('internal', '0005_remove_member_card_number'),
    ]

    operations = [
        migrations.CreateModel(
            name='Secret',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', web.multilingual.modelfields.MultiLingualTextField(max_length=100, unique=True, verbose_name='title')),
                ('content', web.multilingual.modelfields.MultiLingualRichTextUploadingField(verbose_name='description')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
            ],
        ),
    ]
