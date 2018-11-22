"""
Django settings for iotsignals project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

from iotsignals.settings_common import *  # noqa F403
from iotsignals.settings_common import INSTALLED_APPS
from iotsignals.settings_common import REST_FRAMEWORK # noqa

from iotsignals.settings_database import (
    LocationKey,
    get_docker_host,
    get_database_key,
    OVERRIDE_HOST_ENV_VAR,
    OVERRIDE_PORT_ENV_VAR,
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TIME_ZONE = 'Europe/Amsterdam'
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
insecure_key = "insecure"
SECRET_KEY = os.getenv("SECRET_KEY", insecure_key)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = SECRET_KEY == insecure_key

ALLOWED_HOSTS = ['*']

# Application definition
HEALTH_MODEL = 'passage.Passage'

INSTALLED_APPS += [
    'health',
    'datetimeutc',
    'iotsignals',
    'passage'
]

# MIDDLEWARE = [
#     'django.middleware.common.CommonMiddleware',
# ]

ROOT_URLCONF = 'iotsignals.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'iotsignals.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

ROOT_URLCONF = "iotsignals.urls"

WSGI_APPLICATION = "iotsignals.wsgi.application"

DATABASE_OPTIONS = {
    LocationKey.docker: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "iotsignals"),
        "USER": os.getenv("DATABASE_USER", "iotsignals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": "database",
        "PORT": "5432",
    },
    LocationKey.local: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "iotsignals"),
        "USER": os.getenv("DATABASE_USER", "iotsignals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": get_docker_host(),
        "PORT": "5432",
    },
    LocationKey.override: {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("DATABASE_NAME", "iotsignals"),
        "USER": os.getenv("DATABASE_USER", "iotsignals"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD", "insecure"),
        "HOST": os.getenv(OVERRIDE_HOST_ENV_VAR),
        "PORT": os.getenv(OVERRIDE_PORT_ENV_VAR, "5432"),
    }
}

DATABASES = {
    "default": DATABASE_OPTIONS[get_database_key()],
}


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/iotsignals/static/'
STATIC_ROOT = '/static/'
