from django.contrib import admin

from tools.models import Tool
<<<<<<< HEAD
from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Tool, MultiLingualFieldAdmin)
=======

admin.site.register(Tool)
>>>>>>> 1a41b3b99af06cb8f8814169aa7ab0626fa2439e
