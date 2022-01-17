from django.contrib import admin
from django.template.defaultfilters import urlize
from django.utils.translation import gettext_lazy as _

from util.admin_utils import list_filter_factory
from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Announcement


class AnnouncementAdmin(MultiLingualFieldAdmin):
    list_display = ('content', 'classification', 'site_wide', 'get_is_shown', 'get_link', 'display_from', 'display_to')
    list_filter = (
        'classification', 'site_wide',
        list_filter_factory(
            _("shown"), 'shown', lambda qs, yes_filter: qs.valid() if yes_filter else qs.invalid(),
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
        return announcement.is_valid()

    @admin.display(
        ordering='link',
        description=_("Link"),
    )
    def get_link(self, announcement: Announcement):
        return urlize(announcement.link) or None


admin.site.register(Announcement, AnnouncementAdmin)
