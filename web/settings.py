import logging
import sys
from pathlib import Path

from django.conf.locale.en import formats as en_formats
from django.conf.locale.nb import formats as nb_formats


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
CHECKIN_KEY = ''
REDIS_IP = '127.0.0.1'
REDIS_PORT = 6379
STREAM_KEY = ''

# When using more than one subdomain, the session cookie domain has to be set so
# that the subdomains can use the same session. Currently points to "makentnu.localhost"
# should be changed in production. Cannot use only "localhost", as domains for cookies
# are required to have two dots in them.
SESSION_COOKIE_DOMAIN = ".makentnu.localhost"

# For django-hosts to redirect correctly across subdomains, we have to specify the
# host we are running on. This currently points to "makentnu.localhost:8000", and should
# be changed in production
PARENT_HOST = "makentnu.localhost:8000"

EVENT_TICKET_EMAIL = "ticket@makentnu.no"
EMAIL_SITE_URL = "https://makentnu.no"

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
    'ckeditor',  # must be listed after `web` to make the custom `ckeditor/config.js` apply
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
    'users',

    'util',  # not a "real" app, just a collection of utilities
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
ROOT_HOSTCONF = "web.hosts"
DEFAULT_HOST = "main"

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
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

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
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

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

# Set time format for English to match the Norwegian format
for format_name in ('TIME_FORMAT', 'DATETIME_FORMAT', 'SHORT_DATETIME_FORMAT'):
    format_str: str = getattr(en_formats, format_name)
    setattr(en_formats, format_name, format_str.replace('P', 'H:i'))

nb_formats.DECIMAL_SEPARATOR = '.'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = BASE_DIR.parent / 'static'
STATIC_URL = '/static/'

# ManifestStaticFilesStorage appends every static file's MD5 hash to its filename,
# which avoids waiting for browsers' cache to update if a file's contents change
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'


# Code taken from https://github.com/django-ckeditor/django-ckeditor/issues/404#issuecomment-687778492
def static_lazy(path):
    from django.templatetags.static import static
    from django.utils.functional import lazy

    return lazy(lambda: static(path), str)()


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
        'contentsCss': [
            static_lazy('ckeditor/ckeditor/customstyles.css'),
            static_lazy('ckeditor/ckeditor/contents.css'),  # CKEditor's default styles
        ],
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


# See http://docs.djangoproject.com/en/dev/topics/logging for
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
