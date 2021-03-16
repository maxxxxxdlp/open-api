import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# location of the OpenAPI schema file
OPEN_API_LOCATION = os.path.join(BASE_DIR, '../config/open_api.yaml')

# Location for the error logs and API testing issues
ERROR_LOGS_LOCATION = os.path.join(BASE_DIR, '../logs')
