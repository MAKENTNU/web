from django.db.models.signals import m2m_changed

from .models import InheritanceGroup


def update_permissions(instance: InheritanceGroup, action, reverse, **kwargs):
    if not reverse and action in {'post_add', 'post_remove', 'post_clear'}:
        instance.update_permissions()


def connect():
    m2m_changed.connect(update_permissions, sender=InheritanceGroup.parents.through)
    m2m_changed.connect(update_permissions, sender=InheritanceGroup.own_permissions.through)
