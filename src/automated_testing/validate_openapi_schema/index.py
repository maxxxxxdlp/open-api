import yaml
from src.automated_testing import settings
from openapi_spec_validator import validate_spec

with open(settings.OPEN_API_YAML_LOCATION) as file:
	spec_dict = yaml.safe_load(file.read())

validate_spec(spec_dict)