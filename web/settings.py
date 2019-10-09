import os

# Default values
DATABASE = 'sqlite'
SECRET_KEY = ' '
DEBUG = True
ALLOWED_HOSTS = ['*']
MEDIA_ROOT = '../media/'
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

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_hosts',
    'groups',
    'web',
    'make_queue',
    'social_django',
    'phonenumber_field',
    'news',
    'mail',
    'ckeditor',
    'ckeditor_uploader',
    'contentbox',
    'checkin',
    'sorl.thumbnail',
    'channels',
    'internal',
    'card',
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
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
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

SOCIAL_AUTH_NEW_USER_REDIRECT_URL = SOCIAL_AUTH_LOGIN_REDIRECT_URL

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'nb'

LANGUAGES = (
    ('en', 'English'),
    ('nb', 'Norsk'),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "../static")
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
            {'name': 'insert', 'items': ['Image']},
        ],
        'toolbar': 'main',
        'tabSpaces': 4,
        'extraPlugins': ','.join([
            'uploadimage',
            'image2',
        ])
    }
}

# Phonenumbers
PHONENUMBER_DEFAULT_REGION = 'NO'
PHONENUMBER_DEFAULT_FORMAT = 'NATIONAL'
