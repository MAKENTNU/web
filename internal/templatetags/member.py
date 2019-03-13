from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag()
def get_membership_states(member):
    """
    Returns a list of tuples (Membership state, Display color) of the states of the membership of the given member
    :param member: The member to retrieve states for
    :return: A list of one or two tuples (two if honorary member)
    """
    states = []
    if member.quit:
        states += [(_("Quit"), "red")]
    elif member.retired:
        states += [(_("Pang"), "blue")]
    elif not member.active:
        states += [(_("Inactive"), "grey")]
    else:
        states += [(_("Active"), "green")]

    if member.honorary_member:
        states += [(_("Honorary"), "yellow")]

    return states


@register.simple_tag()
def get_system_accesses(member):
    """
    Returns a list of tuples (Name of system, Has access) of the systems the member could have access to
    :param member: The member to check accesses for
    :return: A list of system accesses with their state
    """
    return [(prop.name, prop.value, [_("No"), _("Yes")][prop.value]) for prop in member.memberproperty_set.all()]


@register.simple_tag()
def get_committees(member):
    """
    Returns a list of tuples (Committee name, Display color) of the committees the given member is a part of
    :param member: The member to find committees for
    :return: A list of committees with display color
    """
    colors = {
        "Dev": "green",
        "Mentor": "red",
        "Event": "blue",
        "PR": "yellow",
        "Styret": "purple",
    }
    return [(committee.name, colors[committee.name]) for committee in member.committees.all()] or ""
