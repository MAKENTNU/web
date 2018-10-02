from django.contrib import admin

from dataporten.login_handlers import register_handler
from make_queue.models import *

# Register your models here.
from make_queue.util.login_handlers import PrinterHandler

admin.site.register(ReservationRule)
admin.site.register(Reservation)
admin.site.register(Machine)

register_handler(PrinterHandler, "printer_allowed")
