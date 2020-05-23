from django.contrib import admin

from makerspace.models import Tool

from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Tool, MultiLingualFieldAdmin)
