from django.views.generic import UpdateView

from contentbox.models import ContentBox


class EditContentBoxView(UpdateView):
    model = ContentBox
    template_name = 'contentbox/edit.html'
    fields = (
        'content',
    )
    success_url = '/'
