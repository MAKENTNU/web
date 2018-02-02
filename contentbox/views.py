from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import UpdateView

from contentbox.models import ContentBox


class EditContentBoxView(PermissionRequiredMixin, UpdateView):
    model = ContentBox
    template_name = 'contentbox/edit.html'
    fields = (
        'content',
    )
    permission_required = (
        'contentbox.change_contentbox',
    )
    success_url = '/'
