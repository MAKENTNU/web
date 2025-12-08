from django import template
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from users.models import User
from ..models import Member

register = template.Library()


@register.simple_tag
def get_membership_statuses(member: Member):
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
def get_system_accesses(member: Member, user: User):
    """
    Returns a list of tuples (Name of system, Has access) of the systems the member could have access to.

    :param member: The member to check accesses for
    :param user: The requesting user
    :return: A list of system accesses with their state
    """
    return [
        (
            access.get_name_display(),
            access.value,
            [_("No"), _("Yes")][access.value],
            access.change_url
            if member.user == user or user.has_perm("internal.change_systemaccess")
            else "",
        )
        for access in member.system_accesses.all()
    ]


# noinspection PyPep8Naming
@register.simple_tag
def color_for_committee(
    committee_name: str, *, MAKE_col_prefixed=False, MAKE_bg_prefixed=False
):
    prefix = ""
    if MAKE_col_prefixed:
        prefix = "make-col-"
    elif MAKE_bg_prefixed:
        prefix = "make-bg-"

    committee_to_color = {
        "dev": "green",
        "event": "blue",
        "mentor": "red",
        "pr": f"{prefix}yellow",
        "styret": "purple",
    }
    return committee_to_color.get(committee_name.lower(), "")


@register.simple_tag
def get_committees(member: Member):
    """
    Returns a list of tuples (Committee name, Display color) of the committees the given member is a part of.

    :param member: The member to find committees for
    :return: A list of committees with display color
    """
    committee_names = sorted(committee.name for committee in member.committees.all())
    if not committee_names:
        return ""

    return [
        (name, color_for_committee(name, MAKE_bg_prefixed=True))
        for name in committee_names
    ]
