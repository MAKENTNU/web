from django.urls import path

from . import views


def get_content_box_urlpatterns(base_template='web/base.html'):
    extra_context = {
        'base_template': base_template,
    }
    return [
        path("<int:pk>/edit/", views.EditContentBoxView.as_view(extra_context=extra_context), name='contentbox_edit'),
    ]
