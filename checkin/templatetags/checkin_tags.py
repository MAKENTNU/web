from django import template
from checkin.models import Profile, Skill, UserSkill, SuggestSkill

register = template.Library()


@register.filter(name='has_voter')
def has_voter(suggestion, user):
    return SuggestSkill.objects.get(title=suggestion).voters.filter(user=user).exists()
