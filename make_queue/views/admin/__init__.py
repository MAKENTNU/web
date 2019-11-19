__all__ = ["course", "quota", "reservation"]

for _import in __all__:
    __import__(f"{__package__}.{_import}")
