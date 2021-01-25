from django.contrib import admin

from web.multilingual.database import MultiLingualFieldAdmin
from .models import Question, Category


class QuestionAdmin(MultiLingualFieldAdmin):
    filter_horizontal = ('categories',)


class CategoryAdmin(MultiLingualFieldAdmin):
    pass


admin.site.register(Question, QuestionAdmin)
