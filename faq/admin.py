from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Category, Question


class QuestionAdmin(MultiLingualFieldAdmin):
    filter_horizontal = ('categories',)


class CategoryAdmin(MultiLingualFieldAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
admin.site.register(Category, CategoryAdmin)
