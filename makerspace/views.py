from django.views.generic import ListView, DetailView, UpdateView, CreateView, DeleteView, TemplateView
from makerspace.models import Makerspace, Tool
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy


class ViewMakerspaceView(TemplateView):
    template_name = 'makerspace/makerspace.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_makerspace_announce'] = Makerspace.objects.last()
        return context


class ViewAdminMakerspaceView(PermissionRequiredMixin, UpdateView):
    model = Makerspace

    template_name = 'makerspace/admin_makerspace.html'
    context_object_name = 'makerspace'
    permission_required = 'makerspace.add_Makerspace'
    fields = "__all__"
    success_url = reverse_lazy('makerspace')


class ViewToolView(DetailView):
    model = Tool
    template_name = 'tools/tool.html'
    context_object_name = 'tool'


class ViewToolsView(ListView):
    model = Tool
    template_name = 'tools/tools.html'
    context_object_name = 'tools_list'


class ViewAdminView(PermissionRequiredMixin, ListView):
    model = Tool
    template_name = 'tools/admin_tool.html'
    context_object_name = 'tools_list'
    permission_required = 'makerspace.add_Tool'


class ViewAdminCreateView(PermissionRequiredMixin, CreateView):
    model = Tool
    template_name = 'tools/admin_tool_create.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.add_Tool'
    fields = "__all__"
    success_url = reverse_lazy('makerspace-tools-admin')


class ViewAdminEditView(PermissionRequiredMixin, UpdateView):
    model = Tool

    template_name = 'tools/admin_tool_edit.html'
    context_object_name = 'tool'
    permission_required = 'makerspace.add_Tool'
    fields = "__all__"
    success_url = reverse_lazy('makerspace-tools-admin')


class ViewDeleteView(DeleteView):
    model = Tool
    success_url = reverse_lazy('makerspace-tools-admin')

    def get(self, request, *args, **argv):
        return self.post(request, *args, **argv)
