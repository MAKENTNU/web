from django.contrib.auth.models import Group, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _


class InheritanceGroup(Group):
    """
    A group that allow inheritance of permissions.

    The groups that a group will inherit from, are given
    by the ``parents`` field.

    The permissions that this group has independently
    from its parents, are given by the ``own_permissions`` field.

    The standard ``permissions`` field will contain the group's own
    permissions, and those it has inherited. This field should not
    be altered, as any change will get overwritten.
    """

    parents = models.ManyToManyField(
        to='self',
        symmetrical=False,
        blank=True,
        related_name='children',
        verbose_name=_("parents"),
    )
    own_permissions = models.ManyToManyField(
        to=Permission,
        blank=True,
        related_name='inheritance_groups',
        verbose_name=_("own permissions"),
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    @property
    def inherited_permissions(self):
        return set(self.permissions.all()) - set(self.own_permissions.all())

    def update_permissions(self):
        """Update the permissions of this group and all its children."""
        own_permissions = list(self.own_permissions.all())

        for parent in self.parents.all():
            own_permissions.extend(parent.permissions.all())

        self.permissions.set(own_permissions)

        for child in self.children.all():
            child.update_permissions()

    def get_all_children(self):
        """Return a queryset of all groups that inherit from this group."""
        children = self.children.all()

        for child in self.children.all():
            children = children.union(child.get_all_children())

        return children

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
        for child in self.get_all_children():
            parents = parents.exclude(pk=child.pk)

        return parents


class Committee(models.Model):
    """
    A committee in the organization.

    A committee gets its name and members through the :model:`groups.InheritanceGroup`
    given in the ``group`` field.
    """

    group = models.OneToOneField(
        to=InheritanceGroup,
        on_delete=models.CASCADE,
        related_name='committee',
        verbose_name=_("group"),
    )
    clickbait = models.TextField(blank=True, verbose_name=_("clickbait"))
    description = models.TextField(verbose_name=_("description"))
    email = models.EmailField(verbose_name=_("email"))
    image = models.ImageField(blank=True, verbose_name=_("image"))
    last_modified = models.DateTimeField(auto_now=True, verbose_name=_("last modified"))

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self.group.name
