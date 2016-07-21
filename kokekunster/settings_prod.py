import os


# Settings for production environment

DEBUG = False

ALLOWED_HOSTS = ['*']  # Should possibly use 'kokekunster.no', 'localhost', '127.0.0.1' instead


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['SECRET_KEY']


# Media files (User-uploaded course logos)

MEDIA_ROOT = '/var/www/kokekunster.no/media/'


# Where manage.py collectstatic copies static files to, and the webserver (e.g. nginx) serves these files

STATIC_ROOT = '/var/www/kokekunter.no/static/'


# Admin settings for proper email sending

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

ADMINS = (
  (os.environ['ADMIN_NAME'], os.environ['ADMIN_EMAIL']),
)