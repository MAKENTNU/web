from django.http import Http404
from django.views.generic import DeleteView


class PureDeleteView(DeleteView):

    def get(self, request, *args, **kwargs):
        # Prevent GET requests to a delete confirmation page,
        # as this view uses a delete confirmation modal instead of a dedicated page
        raise Http404()
