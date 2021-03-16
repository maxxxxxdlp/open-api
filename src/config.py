import os


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

FRONTEND_BASE_DIR = os.path.join(BASE_DIR, '../src/frontend')

TEMPLATES_DIR = os.path.join(BASE_DIR, '../src/frontend/static/templates')

OPEN_API_LOCATION = os.path.join(BASE_DIR, 'open_api.yaml')

ERROR_LOGS_LOCATION = os.path.join(BASE_DIR, '../logs')
