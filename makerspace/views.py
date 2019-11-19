from django.http import Http404
from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView, TemplateView
from makerspace.models import Makerspace, Tool
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from web.templatetags.permission_tags import has_any_tool_permission


class ViewMakerspaceView(TemplateView):
    template_name = 'makerspace/makerspace.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['makerspace_latest'] = Makerspace.objects.last()
        return context


class EditMakerspaceView(PermissionRequiredMixin, UpdateView):
    model = Makerspace
    template_name = 'makerspace/admin_makerspace.html'
    context_object_name = 'makerspace'
    permission_required = 'makerspace.change_makerspace'
    fields = "__all__"
    success_url = reverse_lazy('makerspace')


class ToolView(DetailView):
    model = Tool
    template_name = 'tools/tool.html'
    context_object_name = 'tool'


class ToolsView(ListView):
    model = Tool
    template_name = 'tools/tools.html'
    context_object_name = 'tools_list'


class AdminToolView(TemplateView):
    template_name = 'tools/admin_tool.html'

    def get_context_data(self, **kwargs):
        if not has_any_tool_permission(self.request.user) and not self.request.user.is_superuser:
            raise Http404()
        context = super().get_context_data(**kwargs)
        context.update({
            'tools_list': Tool.objects.all(),
        })
        return context


class CreateToolView(PermissionRequiredMixin, CreateView):
    model = Tool
    template_name = 'tools/admin_tool_create.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.add_tool'
    fields = "__all__"
    success_url = reverse_lazy('makerspace-tools-admin')


class EditToolView(PermissionRequiredMixin, UpdateView):
    model = Tool
    template_name = 'tools/admin_tool_edit.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.change_tool'
    fields = "__all__"
    success_url = reverse_lazy('makerspace-tools-admin')


class DeleteToolView(PermissionRequiredMixin, DeleteView):
    model = Tool
    success_url = reverse_lazy('makerspace-tools-admin')
    permission_required = 'makerspace.delete_tool'

    def get(self, request, *args, **argv):
        return self.post(request, *args, **argv)
