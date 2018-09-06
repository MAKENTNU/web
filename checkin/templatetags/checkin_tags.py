from django import template
from checkin.models import Profile, Skill, UserSkill, SuggestSkill

register = template.Library()


@register.filter(name='has_voter')
def has_voter(suggestion, user):
    return suggestion.voters.filter(user=user).exists()


@register.filter(name='locale_title')
def locale_title(skill, language_code):
    # if isinstance(skill, str):
    #     skill = Skill.objects.get(title=skill)
    return skill.locale_title(language_code)


@register.filter(name='is_admin')
def is_admin(user):
    return user.has_perm("checkin.can_force_suggestion")
