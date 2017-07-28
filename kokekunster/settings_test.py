from .settings import *

# Using an in-memory sqlite3 database for faster testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
