from django.contrib import admin

from dataporten.login_handlers import register_handler
from make_queue.models.models import *
from make_queue.models.course import *

# Register your models here.
from make_queue.util.login_handlers import PrinterHandler

admin.site.register(ReservationRule)
admin.site.register(Reservation)
admin.site.register(Machine)
admin.site.register(Quota)
admin.site.register(Printer3DCourse)

register_handler(PrinterHandler, "printer_allowed")
