__all__ = ["calendar", "machine", "overview", "reservation", "rules"]

for _import in __all__:
    __import__(__package__ + "." + _import)
