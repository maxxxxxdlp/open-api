import os


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

TEMPLATES_DIR = os.path.join(BASE_DIR, 'static/templates')

OPEN_API_LOCATION = os.path.join(BASE_DIR, '../LmRex/config/open_api.yaml')
