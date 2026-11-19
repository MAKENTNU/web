import ipaddress

from django.db import migrations, models

import make_queue.printer_api


def copy_ip_address_to_printer_address(apps, schema_editor):
    # The data is copied through Python instead of changing the column type, as
    # PostgreSQL would convert the `inet` values to strings with a `/32` suffix
    for model_name in ("Machine", "HistoricalMachine"):
        model = apps.get_model("make_queue", model_name)
        for obj in model.objects.exclude(ip_address=None):
            obj.printer_address = obj.ip_address
            obj.save(update_fields=["printer_address"])


def copy_printer_address_to_ip_address(apps, schema_editor):
    for model_name in ("Machine", "HistoricalMachine"):
        model = apps.get_model("make_queue", model_name)
        for obj in model.objects.exclude(printer_address=""):
            try:
                ipaddress.ip_address(obj.printer_address)
            except ValueError:
                # Hostnames can't be stored in the `ip_address` field, so they're lost
                continue
            obj.ip_address = obj.printer_address
            obj.save(update_fields=["ip_address"])


class Migration(migrations.Migration):
    dependencies = [
        ("make_queue", "0036_alter_reservation_options_and_more"),
    ]

    operations = [
        *(
            migrations.AddField(
                model_name=model_name,
                name="printer_address",
                field=models.CharField(
                    blank=True,
                    help_text="The printer's IP address or Tailscale MagicDNS name"
                    " (e.g. “printer-1”), which lets users upload G-code files to the"
                    " printer from the website. Leave empty to disable uploading.",
                    max_length=253,
                    validators=[make_queue.printer_api.validate_printer_address],
                    verbose_name="printer address",
                ),
            )
            for model_name in ("historicalmachine", "machine")
        ),
        migrations.RunPython(
            copy_ip_address_to_printer_address,
            reverse_code=copy_printer_address_to_ip_address,
        ),
        *(
            migrations.RemoveField(model_name=model_name, name="ip_address")
            for model_name in ("historicalmachine", "machine")
        ),
    ]
