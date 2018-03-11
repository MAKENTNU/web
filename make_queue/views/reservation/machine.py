from django.shortcuts import render
from django.views import View

from make_queue.models import Machine


class MachineView(View):
    template_name = "make_queue/reservation_machines.html"

    def get(self, request):
        render_parameters = {'machine_types': [
            {
                'name': machine_type.literal,
                'machines': [machine for machine in machine_type.objects.all()]
            } for machine_type in Machine.__subclasses__() if machine_type.objects.exists()
        ]}

        return render(request, self.template_name, render_parameters)
