# -*- coding: utf-8 -*-
"""
Django settings for chemman project.
"""

import os

from pathlib import Path

from django.contrib.messages import constants as messages
from django.utils.translation import gettext_lazy as _

from core.units import Mass, Volume


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

MESSAGE_TAGS = {
    messages.INFO: '',
    messages.SUCCESS: 'uk-alert-success',
    messages.WARNING: 'uk-alert-warning',
    messages.ERROR: 'uk-alert-danger',
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
# Serve ChemManager using only Gunicorn
SERVE_LAN = os.environ.get('SERVE_LAN', False)

ALLOWED_HOSTS = []

INTERNAL_IPS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Third party apps
    'django_jinja',
    'django_jinja.contrib._humanize',
    'django_spaghetti',
    'rest_framework',
    'django_q',
    # ChemMan apps
    'core',
    'cmrpc',
    'floor_map',
    'msds_collector',
    'operating_instruction_creator',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cmrpc.middlewares.RpcAuthMiddleware',
]

ROOT_URLCONF = 'chemman.urls'

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'core.processors.add_bookmarks',
                'core.processors.add_misc_info',
            ],
            'extensions': [
                'jinja2.ext.do',
                'jinja2.ext.loopcontrols',
                'django_jinja.builtins.extensions.CsrfExtension',
                'django_jinja.builtins.extensions.CacheExtension',
                'django_jinja.builtins.extensions.TimezoneExtension',
                'django_jinja.builtins.extensions.UrlsExtension',
                'django_jinja.builtins.extensions.StaticFilesExtension',
                'django_jinja.builtins.extensions.DjangoFiltersExtension',
                'core.jinja_extensions.I18N',
            ],
            'filters': {
                'unit': 'core.filters.markup_unit',
                'list_url': 'core.filters.list_url',
                'builtin_list': 'core.filters.builtin_list',
                'humanize_mass_vol': 'core.filters.humanize_mass_vol',
                'is_mass': 'core.filters.is_mass',
                'basename': 'core.filters.basename',
            },
            'match_extension': '.html',
            'match_regex': r'^(?!admin/|rest_framework/).*',
            'newstyle_gettext': True,
        },
    },
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
            ],
        },
    },
]

WSGI_APPLICATION = 'chemman.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'chemman.sqlite3',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': BASE_DIR / 'cache',
        'TIMEOUT': 600,
        'OPTIONS': {
            'MAX_ENTRIES': 10000,
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'de-de'

LANGUAGES = [
    ('de', _('German')),
    ('en', _('English')),
]

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'chemman' / 'locale',
    BASE_DIR / 'core' / 'locale',
    BASE_DIR / 'floor_map' / 'locale',
    BASE_DIR / 'msds_collector' / 'locale',
    BASE_DIR / 'operating_instruction_creator' / 'locale',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'cp_static'

START_VIEW = 'core:index'
SHOW_HB_PARAGRAPHS = [1]

MEDIA_ROOT = BASE_DIR / 'uploads'
MEDIA_URL = '/media/'

SESSION_COOKIE_NAME = 'cm_sid'

# Customize for your language
WIKI_LINK = 'https://de.wikipedia.org/wiki/{name}'
WIKI_SEARCH_LINK = 'https://de.wikipedia.org/wiki/Spezial:Suche/{name}'

MSDS_MAXAGE_DAYS = 730
INVENTORY_MAX_AGE = 365
# 10.11.2021 Removed 372 from CMR_HAZARDS
CMR_HAZARDS = ('340', '341', '350', '351', '360', '361', '362')
DEFAULT_VOLUME_UNIT = 'mL'
DEFAULT_MASS_UNIT = 'g'
SHOW_THRESHOLDS = {
    'mass': Mass(1, 'µg'),
    'vol': Volume(1, 'µL'),
}
OBSERVE_AND_WARN = True
INFO_WRONG_BRUTTO = ['admin']
USE_OZONE = True
OZONE_URL = 'http://10.0.0.175:8003/'
OZONE_UID_URL = OZONE_URL + 'core/api/uid/{username}/'
LINK_FIRST_THROUGH_STORAGE = True

# Only served by external server (pure HTML/CSS/JS)
# Set to empty string, to hide the link
PRESENTATION_URL = '/presentations/'

SPAGHETTI_SAUCE = {
    'apps': ['auth', 'core'],
    'show_fields': False,
    'exclude': {'core': ['bookmark', 'employee', 'handbookimage',
                         'listcache', 'journaltype', 'journalentry']},
}

SITE_ID = 1

# Django-Q
Q_CLUSTER = {
    'timeout': 300,
    'retry': 600,
    'queue_limit': 100,
    'max_attempts': 3,
    'orm': 'default',
    'catch_up': False,
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 20,
}

SECRET_FILE = BASE_DIR / '.secret'


def get_secret_key(secret_file):
    try:
        with SECRET_FILE.open('rb') as fp:
            return fp.read()
    except FileNotFoundError:
        secret_key = os.urandom(40)
        with SECRET_FILE.open('wb') as fp:
            fp.write(secret_key)
        return secret_key


SECRET_KEY = get_secret_key(SECRET_FILE)

try:
    from .local_settings import *  # noqa: F401,F403
except ImportError:
    pass

if DEBUG:
    TEMPLATES[0]['OPTIONS']['context_processors'].append(
        'core.processors.add_sql_queries'
    )
