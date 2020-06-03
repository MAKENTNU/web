from django.contrib import admin

from web.multilingual.database import MultiLingualFieldAdmin
from .models import Tool

admin.site.register(Tool, MultiLingualFieldAdmin)
