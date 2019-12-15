from docs.models import Page


class PageByTitle:
    regex = Page.title_regex[1:-1]

    def to_python(self, value):
        try:
            return Page.objects.get(title=value).pk
        except Page.DoesNotExist:
            raise ValueError("No page exists with that title")

    def to_url(self, page):
        return page.title
