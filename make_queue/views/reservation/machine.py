from django.views.generic import TemplateView

from make_queue.models import Machine


class MachineView(TemplateView):
    """View that shows all the machines"""
    template_name = "make_queue/reservation_machines.html"

    def get_context_data(self):
        """
        Creates the context required for the template

        :return: A list of all machine types with a list of their machine if there exists at least one machine of that
                type
        """
        return {"machine_types": [{
            "name": machine_type.literal, "machines": list(machine_type.objects.all())
        } for machine_type in Machine.__subclasses__() if machine_type.objects.exists()]}
