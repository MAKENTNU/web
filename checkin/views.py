from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, CreateView, TemplateView

from checkin.models import Profile, Skill
from web import settings
from django.views.decorators.csrf import csrf_exempt


class CheckInView(TemplateView):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def post(self, request):
        """if request.POST.get('key') == settings.CHECKIN_KEY and Profile.objects.filter(
                card_id=request.POST.get('card_id')).update(on_make=True):"""
        if Profile.objects.filter(card_id=request.POST.get('card_id')).update(on_make=True):
            return HttpResponse()

        return HttpResponse(status=400)


class ViewSkillsView(TemplateView):
    template_name = 'checkin/skills.html'

    def get_context_data(self, **kwargs):

        # Creates dict with skill titles as keys and the highest corresponding skill level as its pair value
        skill_dict = {}
        for profile in Profile.objects.filter(on_make=True):
            for skill in profile.skill.all():
                title, level = skill.title, skill.skill_level
                if title not in skill_dict or level > skill_dict[title]:
                    skill_dict[title] = level

        context = super().get_context_data(**kwargs)
        context.update({
            'skill_dict': skill_dict,
        })
        return context
