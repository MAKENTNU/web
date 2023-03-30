# Generated by Django 4.1.3 on 2022-11-21 03:42

from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("groups", "0012_history_date_db_index"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalInheritanceGroup_own_permissions",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("m2m_history_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "history",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="groups.historicalinheritancegroup",
                    ),
                ),
                (
                    "inheritancegroup",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        db_tablespace="",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="groups.inheritancegroup",
                    ),
                ),
                (
                    "permission",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        db_tablespace="",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="auth.permission",
                    ),
                ),
            ],
            options={
                "verbose_name": "HistoricalInheritanceGroup_own_permissions",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
