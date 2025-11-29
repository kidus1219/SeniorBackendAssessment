import dj_database_url
from .common import *

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = [os.environ['MAIN_ALLOWED_HOST']]

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
}

RATELIMIT_IP_META_KEY = 'HTTP_X_REAL_IP'

CSRF_TRUSTED_ORIGINS = [
    # todo specify trusted domains here for prod
]
CORS_ALLOWED_ORIGINS = [
    # todo specify trusted domains here for prod
]
