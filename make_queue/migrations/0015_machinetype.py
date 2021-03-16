# Generated by Django 3.0.5 on 2020-09-12 22:12
import json
from typing import Union

from django.db import migrations, models
import django.db.models.deletion

import web.multilingual.modelfields
from web.multilingual.data_structures import MultiLingualTextStructure


class MachineTypeStruct:

    def __init__(self, pk: int, name: dict, cannot_use_text: Union[dict, str], usage_requirement: str, has_stream: bool, priority: int):
        self.pk = pk
        self.name = json.dumps(name)
        self.usage_requirement = usage_requirement
        self.has_stream = has_stream
        self.priority = priority

        if isinstance(cannot_use_text, dict):
            self.cannot_use_text = json.dumps(cannot_use_text)
        else:
            self.cannot_use_text = cannot_use_text


default_machine_types = (
    MachineTypeStruct(
        pk=1,
        name={"en": "3D printers", "nb": "3D-printere"},
        cannot_use_text={
            "en": "You must have completed a 3D printer course to reserve the printers."
                  " If you have taken the course, but don't have access, contact 3Dprint@makentnu.no",
            "nb": "Reservasjon av 3D-printere krever fullført 3D-printerkurs."
                  " Hvis du har hatt kurset, men ikke har tilgang, ta kontakt med 3Dprint@makentnu.no",
        },
        usage_requirement="3DPR",
        has_stream=True,
        priority=10,
    ),
    MachineTypeStruct(
        pk=2,
        name={"en": "Sewing machines", "nb": "Symaskiner"},
        cannot_use_text="",
        usage_requirement="AUTH",
        has_stream=False,
        priority=20,
    ),
    MachineTypeStruct(
        pk=3,
        name={"en": "3D scanners", "nb": "3D-skannere"},
        cannot_use_text="",
        usage_requirement="AUTH",
        has_stream=False,
        priority=30,
    ),
    MachineTypeStruct(
        pk=4,
        name={"en": "Workspaces", "nb": "Arbeidsplasser"},
        cannot_use_text="",
        usage_requirement="AUTH",
        has_stream=False,
        priority=5,
    ),
    MachineTypeStruct(
        pk=5,
        name={"en": "Special 3D printers", "nb": "Spesial-3D-printere"},
        cannot_use_text={
            "en": "You must have completed an advanced 3D printer course to reserve the printers."
                  " If you have taken the course, but don't have access, contact 3Dprint@makentnu.no",
            "nb": "Reservasjon av 3D-printere krever fullført avansert 3D-printerkurs."
                  " Hvis du har hatt kurset, men ikke har tilgang, ta kontakt med 3Dprint@makentnu.no",
        },
        usage_requirement="A3DPR",
        has_stream=True,
        priority=15,
    ),
)


def create_default_machine_types(apps, schema_editor):
    MachineType = apps.get_model('make_queue', 'MachineType')
    for machine_type in default_machine_types:
        MachineType.objects.create(
            pk=machine_type.pk,
            name=MultiLingualTextStructure(machine_type.name, True),
            cannot_use_text=MultiLingualTextStructure(machine_type.cannot_use_text, True),
            usage_requirement=machine_type.usage_requirement,
            has_stream=machine_type.has_stream,
            priority=machine_type.priority,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0014_machine_priority'),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', web.multilingual.modelfields.MultiLingualTextField(max_length=30, unique=True)),
                ('cannot_use_text', web.multilingual.modelfields.MultiLingualTextField(blank=True)),
                ('usage_requirement', models.CharField(choices=[('AUTH', 'Only has to be logged in'), ('3DPR', 'Taken the 3D printer course')], default='AUTH', max_length=4, verbose_name='Usage requirement')),
                ('has_stream', models.BooleanField(default=False)),
                ('priority', models.IntegerField(help_text='The machine types are sorted ascending by this value.', verbose_name='Priority')),
            ],
            options={
                'ordering': ['priority'],
            },
        ),
        migrations.RunPython(create_default_machine_types, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='machine',
            name='machine_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='machines', to='make_queue.MachineType', verbose_name='Machine type'),
        ),
        migrations.AlterField(
            model_name='machineusagerule',
            name='machine_type',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='usage_rule', to='make_queue.MachineType'),
        ),
        migrations.AlterField(
            model_name='quota',
            name='machine_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quotas', to='make_queue.MachineType', verbose_name='Machine type'),
        ),
        migrations.AlterField(
            model_name='reservationrule',
            name='machine_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservation_rules', to='make_queue.MachineType', verbose_name='Machine type'),
        ),
    ]
