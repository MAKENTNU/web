from django.contrib import admin


class WebAdminSite(admin.AdminSite):
    apps_listed_first = (
        'users',
        'groups',
        'contentbox',
        'announcements',
        'news',
        'make_queue',
        'makerspace',
        'faq',
        # Apps belonging on other subdomains
        'internal',
        'docs',
        # Non-used (or rarely used) apps
        'checkin',
        'auth',
    )
    _apps__to__index = {app: i for i, app in enumerate(apps_listed_first)}

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label=app_label)

        sort_last_key = len(self.apps_listed_first)

        def app_sorting_key(app_dict: dict):
            # Sorts the apps so that those whose labels are in `apps_listed_first` are listed first,
            # and the rest are sorted last (keeping their original order)
            return self._apps__to__index.get(app_dict['app_label'], sort_last_key)

        app_list.sort(key=app_sorting_key)
        return app_list
