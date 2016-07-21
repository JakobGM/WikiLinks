import os
from kokekunster.settings import BASE_DIR


# Settings for development environment

DEBUG = True


# "Secret" cryptographic key, only used during local development

SECRET_KEY = 'fc4_hb-wi32l^c&qpx6!m)o*xd(4ga$13(ese#pfj#pjxnmt0p'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# For testing email

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'

EMAIL_FILE_PATH = '/tmp/kokekunster_emails'

ADMINS = (
  ('Test Testesen', 'admin_email@domain.tld'),
  ('Testinne Testesen', 'admin_email2@domain.tld'),
)


# User uploaded files (MEDIA)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')