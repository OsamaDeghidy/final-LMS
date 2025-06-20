"""
Django settings for pilot project.

Generated by 'django-admin startproject' using Django 4.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from datetime import timedelta
import os 
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-%9l()dc43djrz=dnah3&#5vxtc7#z2fmh=e$-7m)r*(_svbc2n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesBackend',  # Using AxesBackend instead of AxesStandaloneBackend
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Axes configuration
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Number of failed login attempts before lockout
AXES_COOLOFF_TIME = 1  # 1 hour lockout after too many failed attempts
AXES_LOCKOUT_TEMPLATE = 'account/lockout.html'  # Create this template
AXES_RESET_ON_SUCCESS = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.sites',
    'django.contrib.sites',
    'ckeditor',
    'website',
    'user',
    'user_agents',
    'axes',
    'silk',
    'allauth',  # django-allauth
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    # 'notifications',  # django-notification-hq
    # 'boost',  # django-boost
    'menu_generator',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'website.middleware.UserActivityMiddleware',
    'axes.middleware.AxesMiddleware',
    'pilot.middleware.AdminMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'silk.middleware.SilkyMiddleware',
]

ROOT_URLCONF = 'pilot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',  # django-allauth
                'website.context_processors.categories_processor',  # Add categories to all templates
            ],
        },
    },
]

WSGI_APPLICATION = 'pilot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators



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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/images/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_ROOT = os.path.join(BASE_DIR,'static/images')
STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')

# CKEDITOR_UPLOAD_PATH = 'uploads/'



# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '123',
            'secret': '456',
            'key': ''
        }
    },
    'github': {
        'APP': {
            'client_id': 'ce523861bd1218f092a9',
            'secret': '6633db61a108505fdf303106f835acbc57a79fc1',
            'key': ''
        }
    }
}



# settings.py
AXES_FAILURE_LIMIT = 5  # Maximum failed login attempts allowed
AXES_LOCK_OUT_AT_FAILURE = True  # Lock out IPs after exceeding the failure limit
AXES_COOLOFF_TIME = timedelta(minutes=10)  # Time duration for which an IP is locked out

# Optional: Customize the login URL used by Django Axes
LOGIN_URL = 'user/login/'  # Replace 'your_login_url' with your actual login URL

# settings.py
# AXES_ONLY_USER_FAILURES = False  # Track failed login attempts per IP or per user
AXES_VERBOSE = False  # Whether to log blocked login attempts

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}


