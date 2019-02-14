from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from tools.models import Tool
from django.contrib.auth.mixins import PermissionRequiredMixin

class ViewToolView(DetailView):
    model = Tool
    template_name = 'tools/tool.html'
    context_object_name = 'tool'

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tool = get_object_or_404(Tool, pk=kwargs['pk'])
        context.update({
            'tool': tool,
        })
        return context
    """


class ViewToolsView(ListView):
    model = Tool
    template_name = 'tools/tools.html'
    context_object_name = 'tools_list'

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tools_list': Tool.objects.all()
        })
        return context
    """


class ViewAdminWiev(PermissionRequiredMixin, ListView):
    model = Tool
    template_name = 'tools/admin_tool.html'
    context_object_name = 'tools_list'
    permission_required = 'tools.add_Tool'

    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tools_list': Tool.objects.all()
        })
        return context
    """
