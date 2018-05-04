from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import UpdateView, CreateView, TemplateView

from checkin.models import Profile, Skill, UserSkill, SuggestSkill, RegisterProfile
from web import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime, timedelta


class CheckInView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def post(self, request):
        if request.POST.get('key') == settings.CHECKIN_KEY and Profile.objects.filter(
                card_id=request.POST.get('card_id')).update(on_make=True):
            return HttpResponse()

        return HttpResponse(status=400)


class ShowSkillsView(TemplateView):
    template_name = 'checkin/skills.html'

    def is_checkin_expired(self, profile):
        return (datetime.now() - profile.last_checkin).seconds >= 3600*3

    def check_out_expired(self, profile):
        if self.is_checkin_expired(profile):
            profile.on_make = False
            profile.save()

    def get_context_data(self, **kwargs):
        """ Creates dict with skill titles as keys and
         the highest corresponding skill level as its pair value (quick fix) to show on website """
        # skill_dict = UserSkill.objects.filter(profile__on_make=True).order_by("-skill_level")

        skill_dict = {}

        for profile in Profile.objects.filter(on_make=True):
            self.check_out_expired(profile)
            for level in profile.userskill_set.all():
                title, level_int = level.skill.title, level.skill_level

                if (title not in skill_dict or level_int > skill_dict[title][0]) \
                        and not self.is_checkin_expired(profile):
                    skill_dict[title] = (level_int, profile.last_checkin)

        context = super().get_context_data(**kwargs)
        context.update({
            'skill_dict': sorted(skill_dict.items(), key=lambda x: x[1][1], reverse=True),
        })
        return context


class ProfilePageView(TemplateView):
    template_name = 'checkin/profile.html'

    def post(self, request):
        try:
            rating = int(request.POST.get('rating'))
            skill_id = int(request.POST.get('skill'))
        except ValueError:
            return HttpResponseRedirect(reverse('profile'))

        profile = request.user.profile
        skill = get_object_or_404(Skill, id=skill_id)

        if rating == int(rating) and 0 <= rating <= 3:
            if UserSkill.objects.filter(skill=skill, profile=profile).exists():
                if rating == 0:
                    UserSkill.objects.filter(skill=skill, profile=profile).delete()
                else:
                    UserSkill.objects.filter(skill=skill, profile=profile).update(skill_level=rating)
            elif rating != 0:
                UserSkill.objects.create(skill=skill, profile=profile, skill_level=rating)

        return HttpResponseRedirect(reverse('profile'))

    def get_context_data(self, **kwargs):

        if Profile.objects.filter(user=self.request.user).exists():
            profile = Profile.objects.get(user=self.request.user)
        else:
            profile = Profile.objects.create(user=self.request.user)
        img = profile.image
        userskill_set = profile.userskill_set.all()

        skill_dict = {}
        for us in userskill_set:
            title, level_int = us.skill.title, us.skill_level
            if title not in skill_dict or level_int > skill_dict[title]:
                skill_dict[title] = level_int

        context = super().get_context_data(**kwargs)
        context.update({
            'profile': profile,
            'image': img,
            'userskill': userskill_set,
            'skill_dict': skill_dict,
            'all_skills': Skill.objects.all(),
            'make_member': self.request.user.groups.filter(name="MAKE NTNU").exists(),
        })
        return context


class SuggestSkillView(PermissionRequiredMixin, TemplateView):
    template_name = "checkin/suggest_skill.html"
    permission_required = 'checkin.add_suggestskill'

    def post(self, request):
        suggestion = request.POST.get('suggested-skill')
        profile = request.user.profile
        image = request.FILES.get('image')

        if not suggestion.strip():
            return HttpResponseRedirect(reverse('suggest'))

        if Skill.objects.filter(title=suggestion).exists():
            messages.error(request, "Ferdigheten eksisterer allerede!")
            return HttpResponseRedirect(reverse('suggest'))
        else:
            if SuggestSkill.objects.filter(title=suggestion).exists():
                s = SuggestSkill.objects.get(title=suggestion)
                s.voters.add(profile)
                if s.creator == profile or not s.image:
                    s.image = image
                s.save()
            else:
                sug = SuggestSkill.objects.create(creator=profile, title=suggestion, image=image)
                sug.voters.add(profile)

            if SuggestSkill.objects.get(title=suggestion).voters.count() >= 5 or SuggestSkill.objects.get(title=suggestion).approved:
                Skill.objects.create(title=suggestion, image=image)
                SuggestSkill.objects.get(title=suggestion).delete()
                messages.error(request, "Ferdighet lagt til!")

        return HttpResponseRedirect(reverse('suggest'))

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update({
            'suggestions': SuggestSkill.objects.all(),
        })
        return context


class VoteSuggestionView(PermissionRequiredMixin, TemplateView):
    template_name = "checkin/suggest_skill.html"
    permission_required = 'checkin.add_suggestskill'

    def post(self, request):
        suggestion = SuggestSkill.objects.get(pk=int(request.POST.get('pk')))
        data = {
            'user_exists': suggestion.voters.filter(user=request.user).exists(),
        }
        suggestion.voters.add(request.user.profile)
        data['skill_passed'] = suggestion.voters.count() >= 5 or suggestion.approved
        if data['skill_passed']:
            Skill.objects.create(title=SuggestSkill.objects.get(pk=int(request.POST.get('pk'))).title)
            SuggestSkill.objects.get(pk=int(request.POST.get('pk'))).delete()

        return JsonResponse(data)


class RegisterCardView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def post(self, request):
        card_id = request.POST.get('card_id')
        if not Profile.objects.filter(card_id=card_id).exists():
            RegisterProfile.objects.delete()
            RegisterProfile.objects.create(card_id=card_id, last_scan=datetime.now())
            return HttpResponse()

        return HttpResponse(400)


class RegisterProfileView(TemplateView):

    def post(self, request):
        scan_exists = RegisterProfile.objects.exists()
        data = {
            'scan_exists': scan_exists,
            'scan_is_recent': False,
        }
        if scan_exists:
            scan_is_recent = (datetime.now() - RegisterProfile.objects.first().last_scan) < timedelta(seconds=60)
            data['scan_is_recent'] = scan_is_recent
            if scan_is_recent:
                Profile.objects.filter(user=request.user).update(card_id=RegisterProfile.objects.first().card_id)
        Profile.objects.delete()
        return JsonResponse(data)


class EditProfilePictureView(View):

    def post(self, request):
        image = request.FILES.get('image')
        profile = request.user.profile
        profile.image = image
        profile.save()
        return HttpResponseRedirect(reverse('profile'))


