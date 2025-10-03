import json
import os
from enum import StrEnum
from typing import Final

from dotenv import load_dotenv

# Load the environment variables in the `.env` file
load_dotenv()

_NOT_PROVIDED: Final = object()


class DatabaseSystem(StrEnum):
    POSTGRESQL = "postgres"
    SQLITE = "sqlite"


def get_envvar(name: str, *, default: str = _NOT_PROVIDED) -> str:
    """Returns the environment variable with name ``name``.
    If it doesn't exist and ``default`` has been provided, ``default`` is returned."""
    value = os.environ.get(name)
    if value is None or value == "":
        if default is _NOT_PROVIDED:
            raise KeyError(f"Missing environment variable `{name}`.")
        value = default
    return value


def get_bool_envvar(name: str, *, default: bool = _NOT_PROVIDED) -> bool:
    """Returns the same as ``get_envvar()``, but with the value interpreted as a
    ``bool``: ``True`` if the value equals ``"true"`` (case-insensitive), ``False``
    otherwise."""
    value = get_envvar(
        name,
        default=str(default) if type(default) is bool else default,
    )
    return value.lower() == "true"


# DEV: If a setting *should* be specified in prod, it should *not* have a `default`!

# --- Core settings ---
DEBUG: Final = get_bool_envvar("DEBUG")
SECRET_KEY: Final = get_envvar("SECRET_KEY")
ALLOWED_HOSTS: Final = list(json.loads(get_envvar("ALLOWED_HOSTS")))
INTERNAL_IPS: Final = list(
    json.loads(get_envvar("INTERNAL_IPS", default='["127.0.0.1"]'))
)

# --- Databases ---
DATABASE_SYSTEM: Final = DatabaseSystem(
    get_envvar("DATABASE_SYSTEM", default=DatabaseSystem.SQLITE)
)
SQLITE_DB_PATH: Final = get_envvar("SQLITE_DB_PATH", default="db.sqlite3")
POSTGRES_HOST: Final = get_envvar("POSTGRES_HOST", default="localhost")
POSTGRES_DB_NAME: Final = get_envvar("POSTGRES_DB_NAME", default="make_web")
POSTGRES_DB_USER: Final = get_envvar("POSTGRES_DB_USER", default="devuser")
POSTGRES_DB_PASSWORD: Final = get_envvar("POSTGRES_DB_PASSWORD", default="devpassword")

# --- `django-hosts` ---
PARENT_HOST: Final = get_envvar("PARENT_HOST")

# --- Cookies ---
COOKIE_DOMAIN: Final = get_envvar("COOKIE_DOMAIN")
COOKIE_SECURE: Final = get_bool_envvar("COOKIE_SECURE")

# --- Static and media files ---
STATIC_AND_MEDIA_FILES__PARENT_DIR: Final = get_envvar(
    "STATIC_AND_MEDIA_FILES__PARENT_DIR"
)
# The max size in prod is 50 MiB (through Nginx)
MEDIA_FILE_MAX_SIZE__MB: Final = int(get_envvar("MEDIA_FILE_MAX_SIZE__MB", default="25"))

# --- `channels` ---
REDIS_HOST: Final = get_envvar("REDIS_HOST", default="localhost")
REDIS_PORT: Final = int(get_envvar("REDIS_PORT", default="6379"))

# --- Emailing ---
EMAIL_HOST: Final = get_envvar("EMAIL_HOST")
EMAIL_HOST_USER: Final = get_envvar("EMAIL_HOST_USER")
EMAIL_PORT: Final = int(get_envvar("EMAIL_PORT"))
EMAIL_USE_TLS: Final = get_bool_envvar("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL: Final = get_envvar("DEFAULT_FROM_EMAIL")
SERVER_EMAIL: Final = get_envvar("SERVER_EMAIL")
EMAIL_SUBJECT_PREFIX: Final = get_envvar("EMAIL_SUBJECT_PREFIX")
ADMINS: Final = [
    (full_name, email) for full_name, email in json.loads(get_envvar("ADMINS"))
]

# --- Dataporten/Feide ---
USE_DATAPORTEN_AUTH: Final = get_bool_envvar("USE_DATAPORTEN_AUTH")
SOCIAL_AUTH_DATAPORTEN_KEY: Final = get_envvar("SOCIAL_AUTH_DATAPORTEN_KEY")
SOCIAL_AUTH_DATAPORTEN_SECRET: Final = get_envvar("SOCIAL_AUTH_DATAPORTEN_SECRET")

# --- Checkin ---
CHECKIN_KEY: Final = get_envvar("CHECKIN_KEY")
