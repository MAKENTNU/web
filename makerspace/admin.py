from django.contrib import admin

from web.multilingual.database import MultiLingualFieldAdmin
from .models import Equipment

admin.site.register(Equipment, MultiLingualFieldAdmin)
