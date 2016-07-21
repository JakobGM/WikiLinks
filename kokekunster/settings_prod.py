import os


# Settings for production environment

DEBUG = False


# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.environ['SECRET_KEY']


# Media files (User-uploaded course logos)

MEDIA_ROOT = '/var/www/kokekunster.no/media/'


# Admin settings for proper email sending

ADMINS = (
  (os.environ['ADMIN_NAME'], os.environ['ADMIN_EMAIL']),
)