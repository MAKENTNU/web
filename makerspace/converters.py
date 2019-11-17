from django.shortcuts import get_object_or_404

from makerspace.models import Makerspace


class ToolByTitleConverter:
    regex = "([-0-9A-Za-zÆØÅæøå.]*)"

    def to_python(self, value):
        return get_object_or_404(Makerspace, title=value)

    def to_url(self, value):
        return value.title