import os
import dj_database_url
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY SETTINGS
SECRET_KEY = 'django-insecure-5n9)y(u3g%8i2h&zska##(7f-rzyqnmm)#b_e@ryazy#izd^vp'
DEBUG = 'RENDER' not in os.environ # Deployment ke baad isay False karein
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts.apps.AccountsConfig',
    'security',
    'dashboard',
    'core',
    'purchasing',
    'utilities.apps.UtilitiesConfig',
    'inventory.apps.InventoryConfig',
    'sale',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # CSS theek karne ke liye zaroori hai
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ERP.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "security.context_processors.sidebar_permissions",
            ],
        },
    },
]

WSGI_APPLICATION = 'ERP.wsgi.application'
if 'RENDER' in os.environ:
    # Render (Online) settings
    DATABASES = {
        'default': dj_database_url.config(
            default='postgres://saas_db_kh8v_user:XJ3JoIWfEIfyQrq8oME3yhn6HeUj2Oj2@dpg-d77u4unkijhs73fs9nlg-a.oregon-postgres.render.com/saas_db_kh8v',
            conn_max_age=600
        )
    }
else:
    # Local Settings (SQLite use hoga)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# STATIC FILES (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# WhiteNoise settings for production static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SESSION_COOKIE_AGE = 1209600          # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True
LOGIN_REDIRECT_URL = 'home'
STATICFILES_DIRS = [
    BASE_DIR / "static"
]