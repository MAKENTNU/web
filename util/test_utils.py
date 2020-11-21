import functools
from typing import Any, Dict, Tuple

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission
from django.test import TestCase


# A very small JPEG image without any content; used for mocking a valid image while testing
MOCK_JPG_RAW = b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04' \
               b'\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10' \
               b'\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11' \
               b'\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'

MOCK_JPG_FILE = SimpleUploadedFile(name="img.jpg", content=MOCK_JPG_RAW, content_type='image/jpeg')


def mock_module_attrs(module_and_attrname_to_newattr: Dict[Tuple[Any, str], Any]):
    """
    A decorator for monkey patching attributes of modules while the decorated function is executed;
    the original module attributes are monkey patched back after execution.

    This can be useful when testing code that e.g. calls functions that are hard to mock;
    these functions can instead be replaced by mock functions.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            module_and_attrname_to_oldattr = {}
            for module_and_attrname, new_attr in module_and_attrname_to_newattr.items():
                module, attr_name = module_and_attrname
                module_and_attrname_to_oldattr[module_and_attrname] = getattr(module, attr_name)
                setattr(module, attr_name, new_attr)

            value = func(*args, **kwargs)

            for module_and_attrname, old_attr in module_and_attrname_to_oldattr.items():
                module, attr_name = module_and_attrname
                setattr(module, attr_name, old_attr)

            return value

        return wrapper

    return decorator

class PermissionsTestCase(TestCase):

    def add_permission(self, codename):
        permission = Permission.objects.get(codename=codename)
        self.user.user_permissions.add(permission)
