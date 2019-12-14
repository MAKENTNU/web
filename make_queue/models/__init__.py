__all__ = ["course", "models"]

for _import in __all__:
    __import__(f"{__package__}.{_import}")
