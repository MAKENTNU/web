from django.shortcuts import get_object_or_404
from django.views.generic import UpdateView, CreateView, TemplateView

from checkin.models import Profile, Skill


class TemporaryView(TemplateView):
    template_name = 'checkin/temp.html'

    def get_context_data(self, **kwargs):
        first_profile = Profile.objects.first()

        context = super().get_context_data(**kwargs)
        context.update({
            'profile': first_profile.card_id,
            'skill': first_profile.skill.first().title,
            'skill_level': first_profile.skill.first().skill_level,
            'image': first_profile.image,
        })
        return context
