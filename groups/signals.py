from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import InheritanceGroup


@receiver(m2m_changed, sender=InheritanceGroup.parents.through)
@receiver(m2m_changed, sender=InheritanceGroup.own_permissions.through)
def update_permissions(instance, action, reverse, **kwargs):
    if not reverse and action in ['post_add', 'post_remove', 'post_clear']:
        instance.update_permissions()
