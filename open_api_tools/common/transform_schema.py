"""OpenAPI schema converters and transformers."""


import re
import json
from jsonschema import validate
from openapi_schema_to_json_schema import to_json_schema
from typing import Dict


def resolve_schema_references(open_api):
    """Resolve the $ref objects in the OpenAPI schema.

    Warning: this function uses a naїve string substitution approach, which
    won't work for structures that have a circular reference wth themself.

    Args:
        open_api: OpenAPI Schema v3.0

    Returns:
        Resolved OpenAPI schema
    """
    open_api_string = json.dumps(open_api)
    pattern = re.compile(r"{\"\$ref\": \"#\/components\/(\w+)\/(\w+)\"}")

    for (component_group, component_name) in \
        re.findall(pattern, open_api_string):
        try:
            component = open_api['components'][component_group][component_name]
        except KeyError:
            raise Exception(
                f"Unable to find the definition for the '{component_group}/"
                f"{component_name}' OpenAPI component"
            )

        open_api_string = open_api_string.replace(
            f'{"{"}"$ref": "#/components/{component_group}/'
            f'{component_name}"{"}"}',
            json.dumps(component)
        )

    return json.loads(open_api_string)


def validate_object(
    schema: Dict[str,any],
    components: Dict[str, any],
    content: str,
    mime_type: str
):
    """Validate a response object or request body object.

    ...by transforming it to JSON schema first.

    Args:
        schema:
            OpenAPI schema for an object
            The schema should not include content type keys or response codes
        components:
            The OpenAPI components that may be used in the schema object
        content:
            The content to validate (response object or request body object)
        mime_type:
            The mime type of the content to validate
    """
    if mime_type == 'application/json':
        resolved_schema = resolve_schema_references(dict(
            schema=schema,
            components=components
        ))['schema']
        json_schema = \
            to_json_schema(resolved_schema)

        # Make sure the response is a valid JSON object
        json_content = json.loads(content)

        # Test the response against JSON schema
        validate(json_content, json_schema)
    else:
        # It doesn't yet validate non JSON responses
        pass
