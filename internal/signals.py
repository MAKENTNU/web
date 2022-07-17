from django.db.models.signals import m2m_changed

from groups.models import Committee
from .models import Member


def member_update_user_groups(instance: Member, action, pk_set=None, **kwargs):
    """
    Makes sure that the member is added/removed from the correct groups as their committee membership changes.
    """
    if action in {'pre_add', 'pre_remove'}:
        committees = Committee.objects.filter(pk__in=pk_set)
        if action == 'pre_add':
            for committee in committees:
                committee.group.user_set.add(instance.user)
        elif action == 'pre_remove':
            for committee in committees:
                committee.group.user_set.remove(instance.user)


def connect():
    m2m_changed.connect(member_update_user_groups, sender=Member.committees.through)
