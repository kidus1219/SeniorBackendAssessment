import dj_database_url
from .common import *

DEBUG = True

# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://localhost:8000'
]
CORS_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
]
CORS_ALLOW_ALL_ORIGINS = True  # todo - this only have to be inside dev not prod!!
