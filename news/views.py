from django.views.generic import UpdateView, CreateView, TemplateView

from news.models import Article, Event


class AllView(TemplateView):
    template_name = 'news/all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.filter(event=None),
            'events': Event.objects.all(),
        })
        return context


class EditArticleView(UpdateView):
    model = Article
    template_name = 'news/article_edit.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
    )
    success_url = '/'


class CreateArticleView(CreateView):
    model = Article
    template_name = 'news/article_create.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
    )
    success_url = '/'


class EditEventView(UpdateView):
    model = Event
    template_name = 'news/event_edit.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
        'start_date',
        'end_date',
        'start_time',
        'end_time',
        'place',
        'place_url',
        'hoopla',
    )
    success_url = '/'


class CreateEventView(CreateView):
    model = Event
    template_name = 'news/event_create.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
        'start_date',
        'end_date',
        'start_time',
        'end_time',
        'place',
        'place_url',
        'hoopla',
    )
    success_url = '/'
