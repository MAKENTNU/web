from django.contrib import admin

from makerspace.models import Makerspace, Tool

from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Makerspace, MultiLingualFieldAdmin)
admin.site.register(Tool, MultiLingualFieldAdmin)
