from django.contrib import admin

from web.multilingual.database import MultiLingualFieldAdmin
from .models import Question, Category


class QuestionAdmin(MultiLingualFieldAdmin):
    filter_horizontal = ('categories',)


admin.site.register(Category)
admin.site.register(Question, QuestionAdmin)
