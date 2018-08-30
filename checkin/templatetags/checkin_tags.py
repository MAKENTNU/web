from django import template
from checkin.models import Profile, Skill, UserSkill, SuggestSkill

register = template.Library()


@register.filter(name='has_voter')
def has_voter(suggestion, user):
    return suggestion.voters.filter(user=user).exists()


@register.filter(name='locale_title')
def locale_title(suggestion_skill, language_code):
    return suggestion_skill.locale_title(language_code)
