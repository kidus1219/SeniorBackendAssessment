import os

if os.environ.get('DJANGO_SETTINGS_MODULE') == 'main.settings.dev':
    BASE_MEDIA_URL = '/media/'
    BASE_MEDIA_ROOT = 'media'
    DEBUG_DOT_LOG_PATH = './debug.log'
else:
    BASE_MEDIA_URL = os.environ['BASE_MEDIA_URL']  # /media/
    BASE_MEDIA_ROOT = os.environ['BASE_MEDIA_ROOT']
    DEBUG_DOT_LOG_PATH = os.environ['DEBUG_DOT_LOG_PATH']
