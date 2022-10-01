# Generated by Django 4.1.3 on 2022-11-21 04:00

import datetime
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import internal.modelfields
import internal.validators
import phonenumber_field.modelfields
import re
import simple_history.models
import web.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ("groups", "0012_history_date_db_index"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("internal", "0023_rename_gmail_member_google_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalMember",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "role",
                    web.modelfields.UnlimitedCharField(blank=True, verbose_name="role"),
                ),
                (
                    "contact_email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="contact email"
                    ),
                ),
                (
                    "google_email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="Google email"
                    ),
                ),
                (
                    "MAKE_email",
                    models.EmailField(
                        blank=True,
                        max_length=254,
                        validators=[
                            internal.validators.WhitelistedEmailValidator(
                                valid_domains=["makentnu.no"]
                            )
                        ],
                        verbose_name="MAKE email",
                    ),
                ),
                (
                    "phone_number",
                    phonenumber_field.modelfields.PhoneNumberField(
                        blank=True,
                        max_length=32,
                        region=None,
                        verbose_name="phone number",
                    ),
                ),
                (
                    "study_program",
                    web.modelfields.UnlimitedCharField(
                        blank=True, verbose_name="study program"
                    ),
                ),
                (
                    "ntnu_starting_semester",
                    internal.modelfields.SemesterField(
                        blank=True,
                        help_text="Must be in the format [V/H][year], e.g. “V17” or “H2017”.",
                        null=True,
                        verbose_name="starting semester at NTNU",
                    ),
                ),
                (
                    "date_joined",
                    models.DateField(
                        default=datetime.datetime.now, verbose_name="date joined"
                    ),
                ),
                (
                    "date_quit_or_retired",
                    models.DateField(
                        blank=True, null=True, verbose_name="date quit or retired"
                    ),
                ),
                (
                    "reason_quit",
                    models.TextField(blank=True, verbose_name="reason quit"),
                ),
                ("comment", models.TextField(blank=True, verbose_name="comment")),
                ("active", models.BooleanField(default=True, verbose_name="is active")),
                (
                    "guidance_exemption",
                    models.BooleanField(
                        default=False, verbose_name="guidance exemption"
                    ),
                ),
                ("quit", models.BooleanField(default=False, verbose_name="has quit")),
                ("retired", models.BooleanField(default=False, verbose_name="retired")),
                (
                    "honorary",
                    models.BooleanField(default=False, verbose_name="honorary"),
                ),
                (
                    "github_username",
                    web.modelfields.UnlimitedCharField(
                        blank=True, verbose_name="GitHub username"
                    ),
                ),
                (
                    "discord_username",
                    web.modelfields.UnlimitedCharField(
                        blank=True,
                        help_text="The username must include the hashtag and the four digits at the end.",
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^(.+)#([0-9]{4})$"),
                                "Enter a valid Discord username - including the hashtag and the four digits at the end.",
                            )
                        ],
                        verbose_name="Discord username",
                    ),
                ),
                (
                    "minecraft_username",
                    web.modelfields.UnlimitedCharField(
                        blank=True, verbose_name="Minecraft username"
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical member",
                "verbose_name_plural": "historical members",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalMember_committees",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("m2m_history_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "committee",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        db_tablespace="",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="groups.committee",
                    ),
                ),
                (
                    "history",
                    models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="internal.historicalmember",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        db_tablespace="",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="internal.member",
                    ),
                ),
            ],
            options={
                "verbose_name": "HistoricalMember_committees",
            },
        ),
    ]