import os


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

FRONTEND_BASE_DIR = os.path.join(BASE_DIR, '../frontend')

TEMPLATES_DIR = os.path.join(BASE_DIR, '../frontend/static/templates')

OPEN_API_LOCATION = os.path.join(BASE_DIR, 'open_api.yaml')

ERROR_LOGS_LOCATION = os.path.join(BASE_DIR, '../automated_testing/error_logs')