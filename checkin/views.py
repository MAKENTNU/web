from dataclasses import dataclass
from datetime import timedelta
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from card import utils as card_utils
from card.views import RFIDView
from .models import Profile, RegisterProfile, Skill, SuggestSkill, UserSkill


class CheckInView(RFIDView):

    def card_number_valid(self, card_number):
        profiles = Profile.objects.filter(user__card_number=card_number)
        if not profiles.exists():
            return HttpResponse(f"{escape(card_number)} is not registered", status=HTTPStatus.UNAUTHORIZED)

        if profiles.first().on_make:
            profiles.update(on_make=False)
            return HttpResponse('check out'.encode(), status=HTTPStatus.OK)
        else:
            profiles.update(on_make=True, last_checkin=timezone.now())
            return HttpResponse('check in'.encode(), status=HTTPStatus.OK)


class ShowSkillsView(TemplateView):
    template_name = 'checkin/skills.html'
    expiry_time = (60 * 60) * 3

    def is_checkin_expired(self, profile):
        return (timezone.now() - profile.last_checkin).seconds >= self.expiry_time

    def check_out_expired(self, profile):
        if self.is_checkin_expired(profile):
            profile.on_make = False
            profile.save()

    def get_context_data(self, **kwargs):
        """
        Creates dict with skill titles as keys and
        the highest corresponding skill level as its pair value (quick fix) to show on website.
        """
        # skill_dict = UserSkill.objects.filter(profile__on_make=True).order_by("-skill_level")

        skill_dict = {}

        for profile in Profile.objects.filter(on_make=True):
            self.check_out_expired(profile)
            for user_skill in profile.user_skills.all():
                skill = user_skill.skill

                if ((skill not in skill_dict
                     or skill.skill_level > skill_dict[skill][0])
                        and not self.is_checkin_expired(profile)):
                    skill_dict[skill] = (user_skill.skill_level, profile.last_checkin)

        context = super().get_context_data(**kwargs)
        context.update({
            'skill_dict': sorted(skill_dict.items(), key=lambda item: item[1][1], reverse=True),
        })
        return context


@dataclass
# `[...]DataClass` might have been a better name, but `[...]Struct` is shorter
class CompletedCourseMessageStruct:
    completed: bool
    message: str
    usage_hint: str = None


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

        if 0 <= rating <= 3:
            if UserSkill.objects.filter(skill=skill, profile=profile).exists():
                if rating == 0:
                    UserSkill.objects.filter(skill=skill, profile=profile).delete()
                else:
                    UserSkill.objects.filter(skill=skill, profile=profile).update(skill_level=rating)
            elif rating != 0:
                UserSkill.objects.create(skill=skill, profile=profile, skill_level=rating)

        return HttpResponseRedirect(reverse('profile'))

    def get_context_data(self, **kwargs):
        user = self.request.user
        profile, _created = Profile.objects.get_or_create(user=user)

        completed_3d_printer = hasattr(user, 'printer_3d_course')
        completed_raise3d = completed_3d_printer and user.printer_3d_course.raise3d_course
        completed_sla = completed_3d_printer and user.printer_3d_course.sla_course

        completed_course_message_structs = [
            CompletedCourseMessageStruct(
                completed=completed_3d_printer,
                message=(_("You have completed the 3D printer course") if completed_3d_printer
                         else _("You have not taken the 3D printer course")),
                usage_hint=_(
                    "To use a 3D printer, make a reservation in the calendar of one of the 3D printers on the “Reservations” page."
                ) if completed_3d_printer else None,
            ),
            CompletedCourseMessageStruct(
                completed=completed_raise3d,
                message=(_("You have completed the Raise3D printer course") if completed_raise3d
                         else _("You have not taken the Raise3D printer course")),
                usage_hint=_(
                    "To use a Raise3D printer, make a reservation in the calendar of one of the Raise3D printers on the “Reservations” page."
                ) if completed_raise3d else None,
            ),
            CompletedCourseMessageStruct(
                completed=completed_sla,
                message=(_("You have completed the SLA 3D printer course") if completed_sla
                         else _("You have not taken the SLA 3D printer course")),
                usage_hint=_(
                    "To use an SLA 3D printer, make a reservation in the calendar of one of the SLA 3D printers on the “Reservations” page."
                ) if completed_sla else None,
            ),
        ]

        """ Commented out because it's currently not in use; see the template code in `profile_internal.html`
        user_skills = profile.user_skills.all()
        skill_dict = {}
        for user_skill in user_skills:
            skill = user_skill.skill
            if skill not in skill_dict or skill.skill_level > skill_dict[skill][0]:
                skill_dict[skill] = user_skill.skill_level
        """

        context = super().get_context_data(**kwargs)
        context.update({
            'profile': profile,
            'completed_course_message_structs': completed_course_message_structs,
            # Commented out for the same reason as above
            # 'userskill': user_skills,
            # 'skill_dict': skill_dict,
            # 'all_skills': Skill.objects.all(),
        })
        return context


class SuggestSkillView(PermissionRequiredMixin, TemplateView):
    permission_required = ('checkin.add_suggestskill',)
    template_name = 'checkin/suggest_skill.html'
    extra_context = {
        'suggestions': SuggestSkill.objects.all(),
    }

    def post(self, request):
        suggestion = request.POST.get('suggested-skill')
        suggestion_english = request.POST.get('suggested-skill-english')
        profile = request.user.profile
        image = request.FILES.get('image')

        if suggestion.strip() and not suggestion_english.strip():
            messages.error(request, _("Enter both norwegian and english skill name"))
            return HttpResponseRedirect(reverse('suggest'))
        elif not suggestion.strip() and suggestion_english.strip():
            messages.error(request, _("Enter both norwegian and english skill name"))
            return HttpResponseRedirect(reverse('suggest'))
        elif not suggestion.strip() and not suggestion_english.strip():
            return HttpResponseRedirect(reverse('suggest'))

        if Skill.objects.filter(title=suggestion).exists() or Skill.objects.filter(
                title_en=suggestion_english).exists():
            messages.error(request, _("Skill already exists!"))
            return HttpResponseRedirect(reverse('suggest'))
        else:
            if SuggestSkill.objects.filter(title=suggestion).exists():
                s = SuggestSkill.objects.get(title=suggestion)
                s.voters.add(profile)
                if s.creator == profile or not s.image:
                    s.image = image
                s.save()
            else:
                # does not work for some reason
                sug = SuggestSkill.objects.create(creator=profile, title=suggestion, title_en=suggestion_english,
                                                  image=image)
                sug.voters.add(profile)

            if SuggestSkill.objects.get(title=suggestion).voters.count() >= 5:
                Skill.objects.create(title=suggestion, image=image)
                SuggestSkill.objects.get(title=suggestion).delete()
                messages.info(request, _("Skill added!"))

        return HttpResponseRedirect(reverse('suggest'))


class VoteSuggestionView(PermissionRequiredMixin, TemplateView):
    permission_required = ('checkin.add_suggestskill',)
    template_name = 'checkin/suggest_skill.html'

    def post(self, request):
        suggestion = SuggestSkill.objects.get(pk=int(request.POST.get('pk')))
        forced = request.POST.get('forced') == "true"
        response_dict = {
            'skill_passed': False,
            'user_exists': suggestion.voters.filter(user=request.user).exists(),
            'is_forced': forced,
        }
        if forced:
            Skill.objects.create(title=suggestion.title, title_en=suggestion.title_en, image=suggestion.image)
            suggestion.delete()
            return JsonResponse(response_dict)

        suggestion.voters.add(request.user.profile)
        response_dict['skill_passed'] = suggestion.voters.count() >= 5
        if response_dict['skill_passed']:
            Skill.objects.create(title=suggestion.title, title_en=suggestion.title_en, image=suggestion.image)
            suggestion.delete()

        return JsonResponse(response_dict)


class DeleteSuggestionView(PermissionRequiredMixin, TemplateView):
    permission_required = ('checkin.delete_suggestskill',)
    template_name = 'checkin/suggest_skill.html'

    def post(self, request):
        data = {"suggestion_deleted": False, }
        SuggestSkill.objects.get(pk=int(request.POST.get('pk'))).delete()
        if not SuggestSkill.objects.filter(pk=int(request.POST.get('pk'))).exists():
            data["suggestion_deleted"] = True

        return JsonResponse(data)


class RegisterCardView(RFIDView):

    def card_number_valid(self, card_number):
        if Profile.objects.filter(user__card__number=card_number).exists():
            return HttpResponse(f"{escape(card_number)} is already registered", status=HTTPStatus.CONFLICT)
        else:
            RegisterProfile.objects.all().delete()
            RegisterProfile.objects.create(card_id=card_number, last_scan=timezone.now())
            return HttpResponse("Card scanned", status=HTTPStatus.OK)


class RegisterProfileView(TemplateView):

    def post(self, request):
        scan_exists = RegisterProfile.objects.exists()
        response_dict = {
            'scan_exists': scan_exists,
            'scan_is_recent': False,
        }
        if scan_exists:
            scan_is_recent = (timezone.now() - RegisterProfile.objects.first().last_scan) < timedelta(seconds=60)
            response_dict['scan_is_recent'] = scan_is_recent
            if scan_is_recent:
                card_number = RegisterProfile.objects.first().card_id
                is_duplicate = card_utils.is_duplicate(card_number, request.user.username)
                if is_duplicate:
                    return HttpResponse(status=HTTPStatus.CONFLICT)
                request.user.card_number = card_number
                request.user.save()
        RegisterProfile.objects.all().delete()
        return JsonResponse(response_dict)


class EditProfilePictureView(View):

    def post(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        profile = request.user.profile
        profile.image = image
        profile.save()
        return HttpResponseRedirect(reverse('profile'))
