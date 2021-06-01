# -*- coding: utf-8 -*-
"""Load the OpenAPI schema `.yaml` file."""

import json
from dataclasses import dataclass
import yaml
from openapi3 import OpenAPI
from openapi_core import create_spec
import urllib
import requests


@dataclass
class Schema:
    """Parsed OpenAPI schema."""

    schema: any
    open_api_core: any


def load_schema(open_api_schema_location: str) -> Schema:
    """Load the OpenAPI schema `.yaml` file.

    Args:
        open_api_schema_location:
            Relative path / absolute path / URLs to a JSON/Yaml OpenAPI
            schema 3.0 file
    """
    try:
        # Try to parse the location as a URL and send a request
        urllib.parse.urlparse(open_api_schema_location)
        schema_string = requests.get(open_api_schema_location).content
    except Exception:
        # Try to read the schema from a local file
        with open(open_api_schema_location) as spec_file:
            schema_string = spec_file.read()

    yaml_spec = yaml.safe_load(schema_string)

    schema = OpenAPI(yaml_spec)

    serializable_spec = json.loads(json.dumps(yaml_spec, default=str))
    open_api_core = create_spec(serializable_spec)

    return Schema(schema=schema, open_api_core=open_api_core)
