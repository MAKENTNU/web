from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from tools.models import Tool


class ViewToolView(TemplateView):
    template_name = 'tools/tool.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tool = get_object_or_404(Tool, pk=kwargs['pk'])
        context.update({
            'tool': tool,
        })
        return context


class ViewToolsView(TemplateView):
    template_name = 'tools/tools.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tools_list': Tool.objects.all()
        })
        return context

class ToolView(TemplateView):
    template_name = 'tools/articles.html'
