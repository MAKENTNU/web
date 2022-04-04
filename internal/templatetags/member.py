from django import template
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag
def get_membership_statuses(member):
    """
    Returns a list of tuples (Membership status, Display color) of the statuses of the membership of the given member.

    :param member: The member to retrieve statuses for
    :return: A list of one or two tuples (two if honorary member)
    """
    statuses = []
    if member.quit:
        # `capfirst()` to avoid duplicate translation differing only in case
        statuses += [(capfirst(_("quit")), "red")]
    elif member.retired:
        statuses += [(capfirst(_("retired")), "blue")]
    elif not member.active:
        statuses += [(capfirst(_("inactive")), "grey")]
    else:
        statuses += [(capfirst(_("active")), "green")]

    if member.honorary:
        statuses += [(capfirst(_("honorary")), "make-bg-yellow")]

    return statuses


@register.simple_tag
def get_system_accesses(member, user):
    """
    Returns a list of tuples (Name of system, Has access) of the systems the member could have access to.

    :param member: The member to check accesses for
    :param user: The requesting user
    :return: A list of system accesses with their state
    """
    return [(
        access.get_name_display(),
        access.value,
        [_("No"), _("Yes")][access.value],
        access.change_url if member.user == user or user.has_perm('internal.change_systemaccess') else "",
    ) for access in member.system_accesses.all()]


@register.simple_tag
def get_committees(member):
    """
    Returns a list of tuples (Committee name, Display color) of the committees the given member is a part of.

    :param member: The member to find committees for
    :return: A list of committees with display color
    """
    colors = {
        "Dev": "green",
        "Mentor": "red",
        "Event": "blue",
        "PR": "make-bg-yellow",
        "Styret": "purple",
    }
    return sorted([(committee.name, colors[committee.name]) for committee in member.committees.all()]) or ""
