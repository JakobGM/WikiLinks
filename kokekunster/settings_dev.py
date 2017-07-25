import os

from kokekunster.settings import BASE_DIR

# Settings for development environment

DEBUG = True

ALLOWED_HOSTS = []


# "Secret" cryptographic key, only used during local development

SECRET_KEY = 'fc4_hb-wi32l^c&qpx6!m)o*xd(4ga$13(ese#pfj#pjxnmt0p'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

# The development database requires postgresql to be installed on the machine.
# The following settings correspond to the default settings used by
# Postgres.app
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['USER'],
        'USER': os.environ['USER'],
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}


# For testing email

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'

EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'tmp', 'email')

ADMINS = (
    ('Test Testesen', 'admin_email@domain.tld'),
    ('Testinne Testesen', 'admin_email2@domain.tld'),
)


# User uploaded files (MEDIA)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Settings for 'dbbackup' app such that it is easy to import production data
# to the dev environment

DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {
    'location': os.path.join(BASE_DIR, 'tmp'),
}

# Use the PK for the localhost Site model here
SITE_ID = 1
