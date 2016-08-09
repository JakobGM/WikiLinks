import os


# Settings for production environment

DEBUG = False

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['SECRET_KEY']

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Media files (User-uploaded course logos)

MEDIA_ROOT = os.environ['MEDIA_ROOT']


# Where manage.py collectstatic copies static files to, and the webserver (e.g. nginx) serves these files

STATIC_ROOT = os.environ['STATIC_ROOT']


# Admin settings for proper email sending

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ADMINS = (
  (os.environ['ADMIN_NAME'], os.environ['ADMIN_EMAIL']),
)

# Backup

DBBACKUP_STORAGE = 'dbbackup.storage.dropbox_storage'
DBBACKUP_TOKENS_FILEPATH = os.environ['TOKENS_FILEPATH']
DBBACKUP_DROPBOX_APP_KEY = os.environ['DROPBOX_APP_KEY']
DBBACKUP_DROPBOX_APP_SECRET = os.environ['DROPBOX_APP_SECRET']