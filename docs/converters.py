from .models import Page
from .validators import page_title_regex


class SpecificPageByTitle:
    regex = page_title_regex.strip(r"^$")

    def to_python(self, value):
        return str(value)

    def to_url(self, page_pk: int):
        return Page.objects.get(pk=page_pk).title
