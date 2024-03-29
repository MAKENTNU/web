from django.contrib import admin
from django.template.defaultfilters import urlize
from django.utils.translation import gettext_lazy as _

from util.admin_utils import DefaultAdminWidgetsMixin, list_filter_factory, search_escaped_and_unescaped
from .models import Announcement


class AnnouncementAdmin(DefaultAdminWidgetsMixin, admin.ModelAdmin):
    list_display = ('content', 'classification', 'site_wide', 'get_is_shown', 'get_link', 'display_from', 'display_to')
    list_filter = (
        'classification', 'site_wide',
        list_filter_factory(
            _("shown"), 'shown', lambda qs, yes_filter: qs.shown() if yes_filter else qs.not_shown(),
        ),
    )
    search_fields = ('content', 'link')
    list_editable = ('classification', 'site_wide')
    ordering = ('-display_from',)

    @admin.display(
        boolean=True,
        description=_("shown"),
    )
    def get_is_shown(self, announcement: Announcement):
        return announcement.is_shown()

    @admin.display(
        ordering='link',
        description=_("link"),
    )
    def get_link(self, announcement: Announcement):
        return urlize(announcement.link) or None

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


admin.site.register(Announcement, AnnouncementAdmin)
