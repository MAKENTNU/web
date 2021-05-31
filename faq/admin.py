from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from util import html_utils
from util.admin_utils import DefaultAdminWidgetsMixin, link_to_admin_change_form, search_escaped_and_unescaped
from .models import Category, Question


class QuestionAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('title', 'get_categories', 'last_modified')
    list_filter = ('categories',)
    search_fields = ('title', 'answer', 'categories__name')
    filter_horizontal = ('categories',)
    readonly_fields = ('last_modified',)

    @admin.display(description=_("Categories"))
    def get_categories(self, question: Question):
        category_strings = [
            link_to_admin_change_form(category)
            for category in question.categories.all()
        ]
        return html_utils.block_join(category_strings, sep="<b>&bull;</b>") or None

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('categories')

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


class CategoryAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


admin.site.register(Question, QuestionAdmin)
admin.site.register(Category, CategoryAdmin)
