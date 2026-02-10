from abc import ABC, abstractmethod

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from ..forms import ArticleForm, NewsBaseForm
from ..models import Article, NewsBase


class ArticleListView(ListView):
    template_name = "news/article/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return (
            Article.objects.published()
            .visible_to(self.request.user)
            .order_by("-publication_time")
        )


class ArticleDetailView(PermissionRequiredMixin, DetailView):
    model = Article
    template_name = "news/article/article_detail.html"
    context_object_name = "news_obj"

    def has_permission(self):
        article = self.get_object()
        if (
            article not in Article.objects.published()
            and not self.request.user.has_perm("news.change_article")
        ):
            return False
        elif article.private and not self.request.user.has_perm(
            "news.can_view_private"
        ):
            return False
        else:
            return True


class AdminArticleListView(PermissionRequiredMixin, ListView):
    model = Article
    template_name = "news/article/admin_article_list.html"
    context_object_name = "articles"

    def has_permission(self):
        return self.request.user.has_any_permissions_for(Article)


class NewsBaseFormMixin(CustomFieldsetFormMixin, ABC):
    model: NewsBase
    form_class: NewsBaseForm
    template_name = "news/news_base_form.html"

    def get_custom_fieldsets(self):
        return [
            {"fields": ("title", "content", "clickbait")},
            self.get_custom_news_fieldset(),
            {"fields": ("image", "contain")},
            {"fields": ("image_description",)},
            {"heading": _("Attributes")},
            {
                "fields": ("featured", "hidden", "private"),
                "layout_class": "ui three inline fields",
            },
        ]

    @abstractmethod
    def get_custom_news_fieldset(self) -> dict:
        raise NotImplementedError


class ArticleFormMixin(NewsBaseFormMixin, ABC):
    model = Article
    form_class = ArticleForm
    success_url = reverse_lazy("admin_article_list")

    back_button_link = success_url
    back_button_text = _("Admin page for articles")

    def get_custom_news_fieldset(self) -> dict:
        return {"fields": ("publication_time",)}


class ArticleUpdateView(PermissionRequiredMixin, ArticleFormMixin, UpdateView):
    permission_required = ("news.change_article",)

    form_title = _("Change Article")


class ArticleCreateView(PermissionRequiredMixin, ArticleFormMixin, CreateView):
    permission_required = ("news.add_article",)

    form_title = _("Add Article")
    save_button_text = _("Add")


class ArticleDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ("news.delete_article",)
    model = Article
    success_url = reverse_lazy("admin_article_list")
