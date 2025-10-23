from dataclasses import dataclass
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from card.views import RFIDView
from util.view_utils import PreventGetRequestsMixin
from .models import Profile, RegisterProfile, Skill, SuggestSkill, UserSkill
from make_queue.models.course import CoursePermission


class AdminCheckInView(RFIDView):
    def card_number_valid(self, card_number):
        profiles = Profile.objects.filter(user__card_number=card_number)
        if not profiles.exists():
            return HttpResponse(
                f"{escape(card_number)} is not registered",
                status=HTTPStatus.UNAUTHORIZED,
            )

        if profiles.first().on_make:
            profiles.update(on_make=False)
            return HttpResponse("check out".encode(), status=HTTPStatus.OK)
        else:
            profiles.update(on_make=True, last_checkin=timezone.now())
            return HttpResponse("check in".encode(), status=HTTPStatus.OK)


class UserSkillListView(TemplateView):
    template_name = "checkin/user_skill_list.html"
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

                if (
                    skill not in skill_dict or skill.skill_level > skill_dict[skill][0]
                ) and not self.is_checkin_expired(profile):
                    skill_dict[skill] = (user_skill.skill_level, profile.last_checkin)

        return {
            **super().get_context_data(**kwargs),
            "skill_dict": sorted(
                skill_dict.items(), key=lambda item: item[1][1], reverse=True
            ),
        }


@dataclass(kw_only=True)
# `[...]DataClass` might have been a better name, but `[...]Struct` is shorter
class CompletedCourseMessageStruct:
    completed: bool
    message: str
    usage_hint: str = None


class ProfileDetailView(TemplateView):
    template_name = "checkin/profile_detail.html"

    def post(self, request):
        try:
            rating = int(request.POST.get("rating"))
            skill_id = int(request.POST.get("skill"))
        except ValueError:
            return HttpResponseRedirect(reverse("profile_detail"))

        profile = request.user.profile
        skill = get_object_or_404(Skill, id=skill_id)

        if 0 <= rating <= 3:
            if UserSkill.objects.filter(skill=skill, profile=profile).exists():
                if rating == 0:
                    UserSkill.objects.filter(skill=skill, profile=profile).delete()
                else:
                    UserSkill.objects.filter(skill=skill, profile=profile).update(
                        skill_level=rating
                    )
            elif rating != 0:
                UserSkill.objects.create(
                    skill=skill, profile=profile, skill_level=rating
                )

        return HttpResponseRedirect(reverse("profile_detail"))

    def get_context_data(self, **kwargs):
        user = self.request.user
        profile, _created = Profile.objects.get_or_create(user=user)

        completed_3d_printer = hasattr(user, "printer_3d_course")
        special_courses = CoursePermission.objects.exclude(
            short_name__in=[
                CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE,
                CoursePermission.DefaultPerms.IS_AUTHENTICATED,
            ]
        )
        completed_course_message_structs = [
            CompletedCourseMessageStruct(
                completed=completed_3d_printer,
                message=(
                    _("You have completed the 3D printer course")
                    if completed_3d_printer
                    else _("You have not taken the 3D printer course")
                ),
                usage_hint=_(
                    "To use a 3D printer, make a reservation in the calendar of one of the 3D printers on the “Reservations” page."
                )
                if completed_3d_printer
                else None,
            ),
            *(
                CompletedCourseMessageStruct(
                    completed=user.printer_3d_course.course_permissions.filter(
                        short_name=c.short_name
                    ).exists(),
                    message=_("You have completed the {} course").format(c.name)
                    if user.printer_3d_course.course_permissions.filter(
                        short_name=c.short_name
                    ).exists()
                    else _("You have not taken the {} course").format(c.name),
                    usage_hint=_(
                        "To use a {}, make a reservation in the calendar of one of the {}s on the “Reservations” page."
                    ).format(c.name, c.name)
                    if user.printer_3d_course.course_permissions.filter(
                        short_name=c.short_name
                    ).exists()
                    else None,
                )
                for c in special_courses
                if hasattr(user, "printer_3d_course")
            ),
        ]

        """ Commented out because it's currently not in use; see the template code in `profile_detail_internal.html`
        user_skills = profile.user_skills.all()
        skill_dict = {}
        for user_skill in user_skills:
            skill = user_skill.skill
            if skill not in skill_dict or skill.skill_level > skill_dict[skill][0]:
                skill_dict[skill] = user_skill.skill_level
        """

        return {
            **super().get_context_data(**kwargs),
            "profile": profile,
            "completed_course_message_structs": completed_course_message_structs,
            # Commented out for the same reason as above
            # 'userskill': user_skills,
            # 'skill_dict': skill_dict,
            # 'all_skills': Skill.objects.all(),
        }


class AdminSuggestSkillView(PermissionRequiredMixin, TemplateView):
    permission_required = ("checkin.add_suggestskill",)
    template_name = "checkin/admin_suggest_skill.html"
    extra_context = {
        "suggestions": SuggestSkill.objects.all(),
    }

    def post(self, request):
        suggestion = request.POST.get("suggested-skill")
        suggestion_english = request.POST.get("suggested-skill-english")
        profile = request.user.profile
        image = request.FILES.get("image")

        if suggestion.strip() and not suggestion_english.strip():
            messages.error(request, _("Enter both norwegian and english skill name"))
            return HttpResponseRedirect(reverse("admin_suggest_skill"))
        elif not suggestion.strip() and suggestion_english.strip():
            messages.error(request, _("Enter both norwegian and english skill name"))
            return HttpResponseRedirect(reverse("admin_suggest_skill"))
        elif not suggestion.strip() and not suggestion_english.strip():
            return HttpResponseRedirect(reverse("admin_suggest_skill"))

        if (
            Skill.objects.filter(title=suggestion).exists()
            or Skill.objects.filter(title_en=suggestion_english).exists()
        ):
            messages.error(request, _("Skill already exists!"))
            return HttpResponseRedirect(reverse("admin_suggest_skill"))
        else:
            if SuggestSkill.objects.filter(title=suggestion).exists():
                s = SuggestSkill.objects.get(title=suggestion)
                s.voters.add(profile)
                if s.creator == profile or not s.image:
                    s.image = image
                s.save()
            else:
                # does not work for some reason
                sug = SuggestSkill.objects.create(
                    creator=profile,
                    title=suggestion,
                    title_en=suggestion_english,
                    image=image,
                )
                sug.voters.add(profile)

            if SuggestSkill.objects.get(title=suggestion).voters.count() >= 5:
                Skill.objects.create(title=suggestion, image=image)
                SuggestSkill.objects.get(title=suggestion).delete()
                messages.success(request, _("Skill added!"))

        return HttpResponseRedirect(reverse("admin_suggest_skill"))


class AdminRegisterCardView(RFIDView):
    def card_number_valid(self, card_number):
        if Profile.objects.filter(user__card__number=card_number).exists():
            return HttpResponse(
                f"{escape(card_number)} is already registered",
                status=HTTPStatus.CONFLICT,
            )
        else:
            RegisterProfile.objects.all().delete()
            RegisterProfile.objects.create(
                card_id=card_number, last_scan=timezone.now()
            )
            return HttpResponse("Card scanned", status=HTTPStatus.OK)


class AdminProfilePictureUpdateView(PreventGetRequestsMixin, View):
    def post(self, request, *args, **kwargs):
        image = request.FILES.get("image")
        profile = request.user.profile
        profile.image = image
        profile.save()
        return HttpResponseRedirect(reverse("profile_detail"))
