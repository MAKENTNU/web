from django.urls import path

from . import views


def get_content_box_urlpatterns(base_template='web/base.html'):
    return [
        path("<int:pk>/edit/", views.EditContentBoxView.as_view(base_template=base_template), name='contentbox_edit'),
    ]
