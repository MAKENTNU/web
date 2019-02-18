from django.contrib.auth.models import Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class InheritanceGroup(Group):
    """
    A group that allow inheritance of permissions.

    The groups that a group will inherit from is given
    by the `parents` field.

    The permissions that this group has independently
    from its parents are given by the `own_permissions` field.

    The standard `permissions` field will contain the groups own
    permissions, and those it has inherited. This field should not
    be altered, as any change will get overwritten.
    """

    parents = models.ManyToManyField(
        'self',
        related_name='sub_groups',
        symmetrical=False,
        blank=True,
    )

    own_permissions = models.ManyToManyField(
        Permission,
        blank=True,
    )

    def update_permissions(self):
        """Update the permissions of this and all sub groups."""
        permissions = list(self.own_permissions.all())

        for parent in self.parents.all():
            permissions += list(parent.permissions.all())

        self.permissions.set(permissions)

        for sub in self.sub_groups.all():
            sub.update_permissions()

    @property
    def inherited_permissions(self):
        return set(self.permissions.all()) - set(self.own_permissions.all())

    def get_sub_groups(self):
        """Return a queryset of all groups that inherits from this group."""
        subs = self.sub_groups.all()

        for sub in self.sub_groups.all():
            subs = subs.union(sub.get_sub_groups())

        return subs

    def get_all_parents(self):
        """Return a queryset of all groups that this group inherits from."""
        parents = self.parents.all()

        for parent in self.parents.all():
            parents = parents.union(parent.get_all_parents())

        return parents

    def get_available_parents(self):
        """
        Return a queryset of all groups that can be a parent to this group.

        This excludes any group that inherits from this group, as that would
        cause a circular dependency.
        """
        parents = InheritanceGroup.objects.exclude(pk=self.pk)
        for sub in self.get_sub_groups():
            parents = parents.exclude(pk=sub.pk)

        return parents


class Committee(models.Model):
    """
    A committee in the organization.

    A committee gets its name and members through the:model:`groups.InheritanceGroup`
    given in the `group` field.
    """

    group = models.OneToOneField(
        InheritanceGroup,
        on_delete=models.CASCADE,
        verbose_name=_('group'),
    )
    description = models.TextField(_('Description'))
    email = models.EmailField(_('Email'))
    image = models.ImageField(_('Image'), blank=True)
    clickbait = models.TextField(
        max_length=300,
        verbose_name=_('Clickbait'),
        blank=True,
    )

    @property
    def name(self):
        return self.group.name

    def __str__(self):
        return self.name
