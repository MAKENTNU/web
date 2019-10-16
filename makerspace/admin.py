from django.contrib import admin

from makerspace.models import MakerSpace

from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(MakerSpace, MultiLingualFieldAdmin)
