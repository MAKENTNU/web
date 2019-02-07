from django.contrib import admin

from tools.models import Tool
from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Tool, MultiLingualFieldAdmin)