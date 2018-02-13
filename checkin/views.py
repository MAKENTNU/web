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


class ShowSkillsView(TemplateView):
    template_name = 'checkin/skills.html'

    def get_context_data(self, **kwargs):

        """ Creates dict with skill titles as keys and
         the highest corresponding skill level as its pair value (quick fix) to show on website """
        skill_dict = {}
        level_list = ["nybegynner", "viderekommen", "ekspert"]
        for profile in Profile.objects.filter(on_make=True):
            for level in profile.userskill_set.all():
                title, level_int = level.skill.title, level.skill_level - 1
                if title not in skill_dict or level_int > level_list.index(skill_dict[title]):
                    skill_dict[title] = level_list[level_int]

        context = super().get_context_data(**kwargs)
        context.update({
            'skill_dict': skill_dict,

        })
        return context


# TODO: create profile page, display profile picture, add and edit skills, multiple dropdown with search,
class ProfilePageView(TemplateView):
    template_name = 'checkin/profile.html'

    def get_context_data(self, **kwargs):
        profile = Profile.objects.first()#get(user=self.request.user)
        img = profile.image
        userskill_set = profile.userskill_set.all()

        skill_dict = {}
        level_list = ["nybegynner", "viderekommen", "ekspert"]
        for us in userskill_set:
            title, level_int = us.skill.title, us.skill_level - 1
            if title not in skill_dict or level_int > level_list.index(skill_dict[title]):
                skill_dict[title] = level_list[level_int]

        context = super().get_context_data(**kwargs)
        context.update({
            'profile': profile,
            'image': img,
            'userskill': userskill_set,
            'skill_dict': skill_dict,
            'all_skills': Skill.objects.all()
        })
        return context
