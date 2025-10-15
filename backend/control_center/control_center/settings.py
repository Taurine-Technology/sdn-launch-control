# File: settings.py
# Copyright (C) 2025 Taurine Technology
#
# This file is part of the SDN Launch Control project.
#
# This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
# available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
#
# Contributions to this project are governed by a Contributor License Agreement (CLA).
# By submitting a contribution, contributors grant Taurine Technology exclusive rights to
# the contribution, including the right to relicense it under a different license
# at the copyright owner's discretion.
#
# Unless required by applicable law or agreed to in writing, software distributed
# under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the GNU General Public License for more details.
#
# For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
# Import database configuration
from .database import get_database_config
from .connection_pool_setup import setup_connection_pool, setup_dev_connection_pool
import environ
import os
import logging.handlers
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
# load environment variables
if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
    print('Found environment variables')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

SECRET_KEY = 'django-insecure-!3w6gt+vcwl(3j4!1!y*u*merg-1ss$q%8(yu6&=+kc5t%btg3'
DEBUG = True
ALLOWED_HOSTS = ['*']

TELEGRAM_API_KEY=env('TELEGRAM_API_KEY')

# Celery Config:
CELERY_BROKER_URL=env("CELERY_BROKER_URL")
# CELERY_BEAT_SCHEDULE = {
#     'aggregate-flows-every-60-seconds': {
#         'task': 'network_data.tasks.aggregate_flows',
#         'schedule': 60.0,
#     },
# }
# Channels configuration: read host and port from environment
CHANNEL_REDIS_HOST = env("CHANNEL_REDIS_HOST", default="redis")
CHANNEL_REDIS_PORT = env.int("CHANNEL_REDIS_PORT", default=6379)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(CHANNEL_REDIS_HOST, CHANNEL_REDIS_PORT)],
            "capacity": 1000,  # Only keep the latest 100 messages per group
            "expiry": 10, # Expire messages after 10 seconds
        },
    },
}

INSTALLED_APPS = [
    'daphne',
    'celery',
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'knox',
    'corsheaders',
    'channels',
    # custom apps
    'network_device',
    'odl',
    'software_plugin',
    'classifier',
    'onos',
    'controller',
    'general',
    'ovs_install',
    'ovs_management',
    'network_data',
    'account',
    'notification',
    'device_monitoring'

]


# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 10000)],
#         },
#     },
# }

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'general.middleware.DatabaseConnectionMiddleware',  # Database connection monitoring
    'general.middleware.ConnectionPoolMiddleware',  # Connection pool management
]

ROOT_URLCONF = 'control_center.urls'

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

WSGI_APPLICATION = 'control_center.wsgi.application'
ASGI_APPLICATION = 'control_center.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases



DATABASES = {
    "default": get_database_config()
}

# Initialize connection pool based on environment
if DEBUG:
    setup_dev_connection_pool()
else:
    setup_connection_pool()

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

CORS_ALLOWED_ORIGINS = [
    "http://10.10.10.2:3000",
    "http://localhost:3000",
]

CORS_ORIGIN_ALLOW_ALL = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': ('knox.auth.TokenAuthentication',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SDN Launch Control API',
    'DESCRIPTION': 'API documentation for SDN Launch Control.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Excludes the schema endpoint from the docs
}

LOG_LEVEL = os.environ.get('DJANGO_LOG_LEVEL', 'INFO')

# Logging configuration with environment variable support for file paths:
# - DJANGO_LOG_FILE: Path for main application log (default: /usr/app/api.log)
# - DJANGO_ERROR_LOG_FILE: Path for error-only log (default: /usr/app/error.log)
# Log rotation: 10MB max file size with 5 backup files

# Define apps that need identical logging config
APP_LOGGERS = [
    'controller', 'general', 'ovs_install', 'ovs_management',
    'software_plugin', 'utils', 'network_device', 'odl', 'onos',
    'account', 'notification', 'device_monitoring', 'network_data', 'classifier'
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('DJANGO_LOG_FILE', '/usr/app/api.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('DJANGO_ERROR_LOG_FILE', '/usr/app/error.log'),
            'formatter': 'verbose',
            'level': 'ERROR',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
    },
    'root': {
        'handlers': ['console', 'file', 'error_file'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        # Only log your apps at INFO or DEBUG, not all of Django
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'WARNING',  # Only show warnings/errors from Django internals
            'propagate': False,
        },
        # Generate identical configs for app loggers
        **{
            app: {
                'handlers': ['console', 'file', 'error_file'],
                'level': LOG_LEVEL,
                'propagate': False,
            }
            for app in APP_LOGGERS
        },
    },
}