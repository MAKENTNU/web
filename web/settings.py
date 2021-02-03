import logging
import sys
from pathlib import Path

# Disable logging when testing
if 'test' in sys.argv:
    # Disable calls with severity level equal to or less than `CRITICAL` (i.e. everything)
    logging.disable(logging.CRITICAL)

# Build paths inside the project like this: BASE_DIR / ...
BASE_DIR = Path(__file__).resolve().parent.parent

# Default values
DATABASE = 'sqlite'
SECRET_KEY = ' '
DEBUG = True
ALLOWED_HOSTS = ['*']
MEDIA_ROOT = BASE_DIR.parent / 'media'
MEDIA_URL = '/media/'
SOCIAL_AUTH_DATAPORTEN_KEY = ''
SOCIAL_AUTH_DATAPORTEN_SECRET = ''
LOGOUT_URL = '/'
LOGIN_URL = '/login'
LOGIN_REDIRECT_URL = '/'
CHECKIN_KEY = ''  # (custom setting)
REDIS_IP = '127.0.0.1'  # (custom setting)
REDIS_PORT = 6379  # (custom setting)
STREAM_KEY = ''  # (custom setting)

# When using more than one subdomain, the session cookie domain has to be set so
# that the subdomains can use the same session. Currently points to "makentnu.localhost"
# should be changed in production. Cannot use only "localhost", as domains for cookies
# are required to have two dots in them.
SESSION_COOKIE_DOMAIN = ".makentnu.localhost"

# For `django-hosts` to redirect correctly across subdomains, we have to specify the
# host we are running on. This currently points to "makentnu.localhost:8000", and should
# be changed in production
PARENT_HOST = "makentnu.localhost:8000"

EVENT_TICKET_EMAIL = "ticket@makentnu.no"  # (custom setting)
EMAIL_SITE_URL = "https://makentnu.no"  # (custom setting)

# Set local settings
try:
    from .local_settings import *
except ImportError:
    pass


INSTALLED_APPS = [
    # Built-in Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages with significant effect on Django's functionality
    'django_hosts',
    'channels',

    # The main entrypoint app
    'web',

    # Other third-party packages
    'social_django',
    'ckeditor',
    'ckeditor_uploader',
    'phonenumber_field',
    'sorl.thumbnail',

    # Project apps, listed alphabetically
    'announcements',
    'card',
    'checkin',
    'contentbox',
    'docs',
    'groups',
    'internal',
    'mail',
    'make_queue',
    'makerspace',
    'news',
    'faq',
    'internal',
    'docs',
    'users',
]

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware',
]


ROOT_URLCONF = 'web.urls'

# `django-hosts` configuration:
ROOT_HOSTCONF = 'web.hosts'
DEFAULT_HOST = 'main'
# All hosted subdomains - defined in `web/hosts.py`
ALL_SUBDOMAINS = (  # (custom setting)
    'i', 'internal', 'internt', 'admin', 'docs', '',
)
# Tells `social-auth-core` (requirement of `python-social-auth`) to allow
# redirection to these host domains after logging in.
# (Undocumented setting; only found in this file:
# https://github.com/python-social-auth/social-core/blob/d66a2469609c7cfd6639b524981689db2f2d5540/social_core/actions.py#L22)
ALLOWED_REDIRECT_HOSTS = [
    f'{subdomain}.{PARENT_HOST}' for subdomain in ALL_SUBDOMAINS
]


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'web.context_processors.login',
            ],
        },
    },
]

ASGI_APPLICATION = 'web.routing.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_IP, REDIS_PORT)],
            # The maximum resend time of a message in seconds
            'expiry': 30,
            # The number of seconds before a connection expires
            'group_expiry': 900,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

if DATABASE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': DATABASE_NAME,
            'USER': DATABASE_USER,
            'PASSWORD': DATABASE_PASSWORD,
            'HOST': 'localhost',
            'PORT': '',
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': str(BASE_DIR / 'db.sqlite3'),
        },
    }

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.User'

# Dataporten

SOCIAL_AUTH_DATAPORTEN_FEIDE_SSL_PROTOCOL = True
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

AUTHENTICATION_BACKENDS = (
    # 'dataporten.social.DataportenFeideOAuth2',
    # 'dataporten.social.DataportenEmailOAuth2',
    'dataporten.social.DataportenOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'email']

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'nb'

LANGUAGES = (
    ('en', 'English'),
    ('nb', 'Norsk'),
)

LOCALE_PATHS = (
    BASE_DIR / 'locale',
)

TIME_ZONE = 'Europe/Oslo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_ROOT = BASE_DIR.parent / 'static'
STATIC_URL = '/static/'

# ManifestStaticFilesStorage appends every static file's MD5 hash to its filename,
# which avoids waiting for browsers' cache to update if a file's contents change
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

CKEDITOR_UPLOAD_PATH = 'ckeditor-upload/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'default': {
        'skin': 'moono-lisa',
        'toolbar_main': [
            {'name': 'basicstyles', 'items': ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter',
                       'JustifyRight', 'JustifyBlock']},
            {'name': 'links', 'items': ['Link', 'Unlink']},
            {'name': 'format', 'items': ['Format', 'RemoveFormat']},
            {'name': 'insert', 'items': ['Image', 'CodeSnippet']},
        ],
        'toolbar': 'main',
        'tabSpaces': 4,
        'extraPlugins': ','.join([
            'codesnippet',
            'uploadimage',
            'image2',
        ]),
    }
}

# Phonenumbers
PHONENUMBER_DEFAULT_REGION = 'NO'
PHONENUMBER_DEFAULT_FORMAT = 'NATIONAL'


# See https://docs.djangoproject.com/en/stable/topics/logging/ for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

"""
Uncomment to print all database queries to the console;
useful for checking e.g. that a request doesn't query the database more times than necessary.
"""
# LOGGING['loggers']['django.db.backends'] = {
#     'level': 'DEBUG',
#     'handlers': ['console'],
# }


# [SHOULD ALWAYS COME LAST] Override the settings above
try:
    from .local_settings_post import *
except ImportError:
    pass
