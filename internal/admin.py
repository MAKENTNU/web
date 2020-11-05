from django.contrib import admin

from internal.models import Member, SecretContent
from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Member)
admin.site.register(SecretContent, MultiLingualFieldAdmin)
