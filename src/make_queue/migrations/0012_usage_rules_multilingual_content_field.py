# Generated by Django 2.1.5 on 2019-03-25 12:13
import json
from django.db import migrations
import web.multilingual.modelfields


def merge_machine_rule_content_fields(apps, schema_editor):
    MachineUsageRule = apps.get_model("make_queue", "MachineUsageRule")
    for rule in MachineUsageRule.objects.all():
        rule.content = json.dumps({
            "nb": rule.content,
            "en": rule.content_en,
        })
        rule.save()


def reverse_merge_machine_rule_content_fields(apps, schema_editor):
    MachineUsageRule = apps.get_model("make_queue", "MachineUsageRule")
    for rule in MachineUsageRule.objects.all():
        content_dict = json.loads(rule.content)
        rule.content = content_dict["nb"]
        rule.content_en = content_dict["en"]
        rule.save()


class Migration(migrations.Migration):
    dependencies = [
        ('make_queue', '0011_quota_default_number_of_reservations'),
    ]

    operations = [
        migrations.RunPython(merge_machine_rule_content_fields, reverse_merge_machine_rule_content_fields),
        migrations.RemoveField(
            model_name='machineusagerule',
            name='content_en',
        ),
        migrations.AlterField(
            model_name='machineusagerule',
            name='content',
            field=web.multilingual.modelfields.MultiLingualRichTextUploadingField(verbose_name='content'),
        ),

    ]
