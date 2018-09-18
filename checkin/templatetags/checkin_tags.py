from django import template
from checkin.models import Profile, Skill, UserSkill, SuggestSkill

register = template.Library()


@register.filter(name='has_voter')
def has_voter(suggestion, user):
    return suggestion.voters.filter(user=user).exists()


@register.filter(name='locale_title')
def locale_title(skill, language_code):
    return skill.locale_title(language_code)


@register.filter(name='can_force_suggestion')
def can_force(user):
    return user.has_perm("checkin.can_force_suggestion")


@register.filter(name='can_delete_suggestion')
def can_delete(user):
    return user.has_perm("checkin.delete_suggestskill")
