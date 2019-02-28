from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from tools.models import Tool
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy


class ViewToolView(DetailView):
    model = Tool
    template_name = 'tools/tool.html'
    context_object_name = 'tool'


class ViewToolsView(ListView):
    model = Tool
    template_name = 'tools/tools.html'
    context_object_name = 'tools_list'


class ViewAdminWiev(PermissionRequiredMixin, ListView):
    model = Tool
    template_name = 'tools/admin_tool.html'
    context_object_name = 'tools_list'
    permission_required = 'tools.add_Tool'


class ViewAdminCreateVeiw(PermissionRequiredMixin, CreateView):
    model = Tool
    template_name = 'tools/admin_tool_create.html'
    context_object_name = 'tool'
    permission_required = 'tools.add_Tool'
    fields = (
        'title',
        'content',
        'image',
    )
    success_url = reverse_lazy('tools/admin')


class ViewAdminEditVeiw(PermissionRequiredMixin, UpdateView):
    model = Tool

    template_name = 'tools/admin_tool_edit.html'
    context_object_name = 'tool'
    permission_required = 'tools.add_Tool'
    fields = (
        'title',
        'content',
        'image',
    )
    success_url = reverse_lazy('tools/admin')
