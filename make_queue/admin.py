from django.contrib import admin
from django.forms import Select

from make_queue.models.course import *
from make_queue.models.models import *


class MachineTypeOverride(admin.ModelAdmin):
    """
    Class used to override the Fomantic UI select widget of the machine type field.
    """

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "machine_type":
            kwargs["widget"] = Select()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


admin.site.register(ReservationRule, MachineTypeOverride)
admin.site.register(Reservation)
admin.site.register(Machine, MachineTypeOverride)
admin.site.register(Quota, MachineTypeOverride)
admin.site.register(Printer3DCourse)
