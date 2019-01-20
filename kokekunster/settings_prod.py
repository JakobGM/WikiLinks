import os
import raven

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
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'database',
        'PORT': '5432',
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

# Using filesystem backup, since the dropbox integration is broken
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': os.path.join(os.path.dirname(os.pardir), 'tmp'),
}
BACKUP_TIMES = ['3:00', '7:00', '12:00', '15:00', '18:00']

# Sentry related settings
RAVEN_CONFIG = {
    'dsn': os.environ['SENTRY_DSN'],
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
}
