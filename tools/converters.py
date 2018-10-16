from django.shortcuts import get_object_or_404

from tools.models import Tool


class ToolbyTitleConverter:
    regex = "([-0-9A-Za-zÆØÅæøå.]*)"

    def to_python(self, value):
        return get_object_or_404(Tool, title=value)

    def to_url(self, value):
        return value.title