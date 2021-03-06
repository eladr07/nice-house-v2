"""
Django settings for NiceHouse project.

Generated by 'django-admin startproject' using Django 2.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'b1&^9&3e48hs#1p+mtypy^8-ho)r%-3^inrp0d9haz0$-xml0o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.elasticbeanstalk.com',
    '195.238.120.210'
    ]


# Application definition

INSTALLED_APPS = [
    'reversion',
    
    'Indices.apps.IndicesConfig',
    'Management.apps.ManagementConfig',
    'Checks.apps.ChecksConfig',
    'Analytics.apps.AnalyticsConfig',
    'Activity.apps.ActivityConfig',
    
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'reversion.middleware.RevisionMiddleware',
]

ROOT_URLCONF = 'NiceHouse.urls'

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

WSGI_APPLICATION = 'NiceHouse.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Management',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'USER': 'root',
        'PASSWORD': "T'z7*L^KKfB7KP8M",
        'ATOMIC_REQUESTS': True
    }
}

# Parse database configuration from $DATABASE_URL
import dj_database_url

db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES['default'].update(db_from_env)


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST_USER = 'nevehair@gmail.com'
EMAIL_HOST_PASSWORD = 'vrqxcozkybgugckw'

SESSION_COOKIE_AGE = 8 * 60 * 60 # 8 Hours

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'he'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    #os.path.join(BASE_DIR, 'static'),
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'form01': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'hand01': {
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/commission.log'), 
            'formatter': 'form01'
        },
        'hand02': {
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/pdf.log'),
            'formatter': 'form01'
        },
        'hand04': {
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/salary.log'), 
            'formatter': 'form01'
        },
        'hand05': {
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/views.log'),
            'formatter': 'form01'
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/error.log'),
            'formatter': 'form01'
        },        
        'query': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/query.log'),
            'formatter': 'form01'
        },
    },
    'loggers': {
        'root': {
            'handlers':['hand01'],
            'propagate': True,
            'level':'DEBUG',
        },
        'commission': {
            'handlers':['hand01'],
            'propagate': True,
            'level':'DEBUG',
        },
        'pdf': {
            'handlers':['hand02'],
            'propagate': True,
            'level':'DEBUG',
        },
        'salary': {
            'handlers':['hand04'],
            'propagate': True,
            'level':'DEBUG',
        },
        'views': {
            'handlers':['hand05'],
            'propagate': True,
            'level':'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['query'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}
