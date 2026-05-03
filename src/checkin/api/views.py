from datetime import timedelta
from http import HTTPStatus

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
from django.utils import timezone
from django.views.generic import DeleteView, TemplateView

from card import utils as card_utils
from checkin.models import RegisterProfile, Skill, SuggestSkill
from util.view_utils import PreventGetRequestsMixin, UTF8JsonResponse


class AdminAPISuggestSkillVoteView(
    PermissionRequiredMixin, PreventGetRequestsMixin, TemplateView
):
    permission_required = ("checkin.add_suggestskill",)

    def post(self, request):
        suggestion = SuggestSkill.objects.get(pk=int(request.POST.get("pk")))
        forced = request.POST.get("forced") == "true"
        response_dict = {
            "skill_passed": False,
            "user_exists": suggestion.voters.filter(user=request.user).exists(),
            "is_forced": forced,
        }
        if forced:
            Skill.objects.create(
                title=suggestion.title,
                title_en=suggestion.title_en,
                image=suggestion.image,
            )
            suggestion.delete()
            return UTF8JsonResponse(response_dict)

        suggestion.voters.add(request.user.profile)

        skill_passed = suggestion.voters.count() >= SuggestSkill.NUM_VOTES_TO_ADD_SKILL
        response_dict["skill_passed"] = skill_passed
        if skill_passed:
            Skill.objects.create(
                title=suggestion.title,
                title_en=suggestion.title_en,
                image=suggestion.image,
            )
            suggestion.delete()

        return UTF8JsonResponse(response_dict)


class AdminAPISuggestSkillDeleteView(
    PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView
):
    permission_required = ("checkin.delete_suggestskill",)
    model = SuggestSkill

    def delete(self, request, *args, **kwargs):
        self.get_object().delete()
        return UTF8JsonResponse({"suggestion_deleted": True})


class AdminAPIRegisterProfileView(PreventGetRequestsMixin, TemplateView):
    def post(self, request):
        scan_exists = RegisterProfile.objects.exists()
        response_dict = {
            "scan_exists": scan_exists,
            "scan_is_recent": False,
        }
        if scan_exists:
            scan_is_recent = (
                timezone.now() - RegisterProfile.objects.first().last_scan
            ) < timedelta(seconds=60)
            response_dict["scan_is_recent"] = scan_is_recent
            if scan_is_recent:
                card_number = RegisterProfile.objects.first().card_id
                is_duplicate = card_utils.is_duplicate(
                    card_number, request.user.username
                )
                if is_duplicate:
                    return HttpResponse(status=HTTPStatus.CONFLICT)
                request.user.card_number = card_number
                request.user.save()
        RegisterProfile.objects.all().delete()
        return UTF8JsonResponse(response_dict)
