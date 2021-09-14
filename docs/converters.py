from .models import Content, Page
from .validators import page_title_regex


class PageByTitle:
    regex = page_title_regex.strip(r"^$")

    def to_python(self, value):
        try:
            return Page.objects.get(title=value).pk
        except Page.DoesNotExist:
            raise ValueError("No page exists with that title")

    def to_url(self, page: Page):
        return page.title


class ContentByPk(object):
    regex = "[0-9]+"

    def to_python(self, value):
        try:
            return Content.objects.get(pk=value)
        except Content.DoesNotExist:
            raise ValueError("No content exists with that PK")

    def to_url(self, content: Content):
        return content.pk
