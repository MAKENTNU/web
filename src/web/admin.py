from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse_lazy

# Virtual admin group name used to display traffic-tracking models under a
# dedicated "Statistics" header instead of mixed in with the `web` app.
STATISTICS_GROUP_LABEL = "statistics"
STATISTICS_GROUP_MODELS = ("PageView", "Visitor")


class WebAdminSite(admin.AdminSite):
    site_url = reverse_lazy("index_page")

    apps_listed_first = (
        "constance",
        # Apps belonging on the main site
        "users",
        "groups",
        "contentbox",
        "announcements",
        "news",
        "make_queue",
        "makerspace",
        "faq",
        # Apps belonging on other subdomains
        "internal",
        "docs",
        STATISTICS_GROUP_LABEL,
        # Non-used (or rarely used) apps
        "checkin",
        "auth",
    )
    _apps__to__index = {app: i for i, app in enumerate(apps_listed_first)}

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)
        app_list = self._extract_statistics_group(app_list)

        sort_last_key = len(self.apps_listed_first)

        def app_sorting_key(app_dict: dict):
            # Sorts the apps so that those whose labels are in `apps_listed_first` are
            # listed first, and the rest are sorted last (keeping their original order)
            return self._apps__to__index.get(app_dict["app_label"], sort_last_key)

        app_list.sort(key=app_sorting_key)
        return app_list

    def _extract_statistics_group(self, app_list):
        """Pulls ``PageView``/``Visitor`` out of the ``web`` app entry into a
        synthetic "Statistics" group so they show up as their own header."""
        web_app = next((a for a in app_list if a["app_label"] == "web"), None)
        if not web_app:
            return app_list

        moved, kept = [], []
        for model in web_app.get("models", []):
            (moved if model["object_name"] in STATISTICS_GROUP_MODELS else kept).append(
                model
            )
        if not moved:
            return app_list

        web_app["models"] = kept
        result = [a for a in app_list if a["app_label"] != "web" or kept]
        result.append(
            {
                "name": _("Statistics"),
                "app_label": STATISTICS_GROUP_LABEL,
                "app_url": "",
                "has_module_perms": True,
                "models": moved,
            }
        )
        return result


class PageViewAdmin(admin.ModelAdmin):
    list_display = ("path", "count", "last_visited")
    search_fields = ("path",)
    readonly_fields = ("path", "count", "last_visited")
    ordering = ("-count",)


class VisitorAdmin(admin.ModelAdmin):
    list_display = ("identifier", "first_seen", "last_seen")
    search_fields = ("identifier",)
    readonly_fields = ("identifier", "first_seen", "last_seen")
    ordering = ("-last_seen",)


def register_models():
    """Registers ``web``-app models on the admin site.

    Called from ``WebConfig.ready()`` to avoid the chicken-and-egg of
    importing ``WebAdminSite`` while the admin module is still loading.
    """
    from web.models import PageView, Visitor

    admin.site.register(PageView, PageViewAdmin)
    admin.site.register(Visitor, VisitorAdmin)
