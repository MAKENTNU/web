from util.url_utils import SpecificObjectConverter
from .models import Article, Event


class SpecificArticle(SpecificObjectConverter):
    model = Article


class SpecificEvent(SpecificObjectConverter):
    model = Event
