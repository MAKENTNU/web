from docs.models import Page, Content


class PageByTitle:
    regex = Page.title_regex[1:-1]

    def to_python(self, value):
        try:
            return Page.objects.get(title=value).pk
        except Page.DoesNotExist:
            raise ValueError("No page exists with that title")

    def to_url(self, page):
        return page.title


class PageByPk:
    regex = "[0-9]+"

    def to_python(self, value):
        try:
            return Page.objects.get(pk=int(value))
        except Page.DoesNotExist:
            raise ValueError("No page exists with that PK")

    def to_url(self, page):
        return page.pk


class ContentByPk(object):
    regex = "[0-9]+"

    def to_python(self, value):
        try:
            return Content.objects.get(pk=value)
        except Content.DoesNotExist:
            raise ValueError("No content exists with that PK")

    def to_url(self, content):
        return content.pk
