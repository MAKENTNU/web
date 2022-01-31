from django.contrib.auth.models import Permission


def get_perm(app_label_and_codename: str):
    """Find the permission object for an <app_label>.<codename> string."""
    app_label, codename = app_label_and_codename.split('.', 1)
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


def perm_to_str(permission: Permission) -> str:
    """Find the <app_label>.<codename> string for a permission object."""
    return f'{permission.content_type.app_label}.{permission.codename}'
