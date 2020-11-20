import functools
from typing import Any, Dict, Tuple


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
