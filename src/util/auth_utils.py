from django.contrib.auth.models import Permission
from django.db.models import Q, QuerySet


def get_perms(*app_labels_and_codenames: str) -> QuerySet[Permission]:
    query = Q()
    for app_label_and_codename in app_labels_and_codenames:
        app_label, codename = app_label_and_codename.split('.', 1)
        query |= Q(content_type__app_label=app_label, codename=codename)
    perms = Permission.objects.filter(query)
    _check_perms(perms, app_labels_and_codenames)
    return perms


def _check_perms(filtered_perms: QuerySet[Permission], perm_strings: tuple[str, ...]):
    if filtered_perms.count() != len(perm_strings):
        perm_strings_set = set(perm_strings)
        if len(perm_strings_set) != len(perm_strings):
            raise ValueError("The permission arguments provided contain duplicates")

        perms_not_found = perm_strings_set - {perm_to_str(perm) for perm in filtered_perms}
        if not perms_not_found:
            # If all the perm arguments were found, it means that the filtered perms contain duplicate
            # combinations of app labels and codenames, in which case it's fine to just return them
            return
        perms_not_found_str = ", ".join(f"'{perm}'" for perm in perms_not_found)
        raise Permission.DoesNotExist(f"The following permissions do not exist: {perms_not_found_str}")


def get_perm(app_label_and_codename: str) -> Permission:
    """Find the permission object for an <app_label>.<codename> string."""
    return get_perms(app_label_and_codename).get()


def perm_to_str(permission: Permission) -> str:
    """Find the <app_label>.<codename> string for a permission object."""
    return f'{permission.content_type.app_label}.{permission.codename}'
