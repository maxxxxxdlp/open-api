"""Load the OpenAPI schema `.yaml` file."""

import json
import yaml
from openapi3 import OpenAPI
from openapi_core import create_spec
import urllib
import requests


def load_schema(open_api_schema_location):
    """Load the OpenAPI schema `.yaml` file."""
    try:
        urllib.parse.urlparse(open_api_schema_location)
        schema_string = requests.get(open_api_schema_location).content
    except Exception:
        with open(open_api_schema_location) as spec_file:
            schema_string = spec_file.read()

    yaml_spec = yaml.safe_load(schema_string)

    schema = OpenAPI(yaml_spec)

    serializable_spec = json.loads(json.dumps(yaml_spec, default=str))
    open_api_core = create_spec(serializable_spec)

    return [schema, open_api_core]
