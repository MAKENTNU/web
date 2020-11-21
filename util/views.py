from django.http import Http404


class PreventGetRequestsMixin:

    def get(self, *args, **kwargs):
        raise Http404()
