# Generated by Django 4.1.7 on 2023-03-24 10:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "internal",
            "0025_secret_extra_view_permissions_and_historicalsecret_extra_view_permissions",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="secret",
            options={
                "permissions": (
                    (
                        "can_view_board_secrets",
                        "Can view secrets that only members of the board need",
                    ),
                    (
                        "can_view_dev_secrets",
                        "Can view secrets that only members of the Dev committee need",
                    ),
                )
            },
        ),
    ]
