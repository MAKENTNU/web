from django.db.models.signals import m2m_changed
from django.dispatch import receiver


def connect():
    # Importing models should not be done in the global scope - which would have caused an `AppRegistryNotReady` exception
    from groups.models import Committee
    from .models import Member

    @receiver(m2m_changed, sender=Member.committees.through)
    def member_update_user_groups(sender, instance: Member, action='', pk_set=None, **kwargs):
        """
        Makes sure that the member is added/removed from the correct groups as their committee membership changes.
        """
        if action == 'pre_add':
            committees = Committee.objects.filter(pk__in=pk_set)
            for committee in committees:
                committee.group.user_set.add(instance.user)
        elif action == 'pre_remove':
            committees = Committee.objects.filter(pk__in=pk_set)
            for committee in committees:
                committee.group.user_set.remove(instance.user)
