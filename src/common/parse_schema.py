import yaml
from openapi3 import OpenAPI
from src import config

with open(config.OPEN_API_LOCATION) as file:
    spec = yaml.safe_load(file.read())

schema = OpenAPI(spec)
