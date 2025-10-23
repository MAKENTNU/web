from django import template

register = template.Library()


@register.filter
def has_voter(suggestion, user):
    return suggestion.voters.filter(user=user).exists()


@register.filter
def locale_title(skill, language_code):
    return skill.locale_title(language_code)


@register.filter
def can_force_suggestion(user):
    return user.has_perm("checkin.can_force_suggestion")


@register.filter
def can_delete_suggestion(user):
    return user.has_perm("checkin.delete_suggestskill")
