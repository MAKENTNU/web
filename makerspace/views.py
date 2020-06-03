from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from web.templatetags.permission_tags import has_any_tool_permissions
from .forms import ToolForm
from .models import Tool


class ToolView(DetailView):
    model = Tool
    template_name = 'tools/tool.html'
    context_object_name = 'tool'


class ToolsView(ListView):
    model = Tool
    template_name = 'tools/tools.html'
    context_object_name = 'tools_list'


class AdminToolView(PermissionRequiredMixin, ListView):
    model = Tool
    template_name = 'tools/admin_tool.html'
    context_object_name = 'tools_list'

    def has_permission(self):
        return has_any_tool_permissions(self.request.user)


class CreateToolView(PermissionRequiredMixin, CreateView):
    model = Tool
    form_class = ToolForm
    template_name = 'tools/admin_tool_create.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.add_tool'
    success_url = reverse_lazy('makerspace-tools-admin')


class EditToolView(PermissionRequiredMixin, UpdateView):
    model = Tool
    form_class = ToolForm
    template_name = 'tools/admin_tool_edit.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.change_tool'
    success_url = reverse_lazy('makerspace-tools-admin')

    # Delete the old image file if a new image is being uploaded:
    def form_valid(self, form):
        if form.files.get('image'):
            tool = self.get_object()
            tool.image.delete()
        return super().form_valid(form)


class DeleteToolView(PermissionRequiredMixin, DeleteView):
    model = Tool
    success_url = reverse_lazy('makerspace-tools-admin')
    permission_required = 'makerspace.delete_tool'

    # Delete the image file before deleting the object:
    def delete(self, request, *args, **kwargs):
        tool = self.get_object()
        tool.image.delete()
        return super().delete(request, *args, **kwargs)
