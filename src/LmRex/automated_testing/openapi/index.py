from json import JSONDecodeError

from openapi_core import create_spec
import yaml
import json
from LmRex.config import frontend_config as settings
from requests import Request, Session
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.validation.response.validators import ResponseValidator
from openapi_core.contrib.requests import RequestsOpenAPIResponseFactory
import urllib.parse as urlparse
from urllib.parse import parse_qs
from LmRex.automated_testing.utils import report_error
from operator import itemgetter

# load the schema
with open(settings.OPEN_API_LOCATION) as file:
    spec_dict = yaml.safe_load(file.read())

serializable_spec = json.loads(json.dumps(spec_dict, default=str))
spec = create_spec(serializable_spec)

# initialize validators
request_validator = RequestValidator(spec)
response_validator = ResponseValidator(spec)
session = Session()


def prepare_request(request_url: str, log_errors: bool = False):
    parsed_url = urlparse.urlparse(request_url)
    base_url = request_url.split('?')[0]
    query_params_dict = parse_qs(parsed_url.query)

    request = Request('GET', base_url, params=query_params_dict)
    openapi_request = RequestsOpenAPIRequest(request)
    request_url_validator = request_validator.validate(openapi_request)

    if request_url_validator.errors:
        error_message = request_url_validator.errors
        error_response = {
            'type':         'invalid_request_url',
            'title':        'Invalid Request URL',
            'error_status': 'Request URL does not meet the' +
                            'OpenAPI Schema requirements',
            'url':          request_url,
            'text':         error_message,
        }
        if log_errors:
            report_error(error_response)
        return error_response

    return {
        'type':            'success',
        'request':         request,
        'openapi_request': openapi_request,
    }


def file_request(request, openapi_request, request_url: str):
    prepared_request = request.prepare()
    response = session.send(prepared_request)

    # make sure that the server did not return an error
    if response.status_code != 200:
        error_response = {
            'type':         'invalid_response_code',
            'title':        'Invalid Response',
            'error_status': 'Response status code indicates an error has occurred',
            'status_code':  response.status_code,
            'url':          request_url,
            'text':         response.text,
        }
        report_error(error_response)
        return error_response

    # make sure the response is a valid JSON object
    try:
        parsed_response = json.loads(response.text)
    except JSONDecodeError:
        error_response = {
            'type':         'invalid_response_mime_type',
            'title':        'Invalid response',
            'error_status': 'Unable to parse JSON response',
            'status_code':  response.status_code,
            'url':          request_url,
            'text':         response.text,
        }
        report_error(error_response)
        return error_response

    # validate the response against the schema
    formatted_response = RequestsOpenAPIResponseFactory.create(response)
    response_content_validator = response_validator.validate(
        openapi_request,
        formatted_response
    )

    if response_content_validator.errors:
        error_message = list(
            map(
                lambda e: e.schema_errors, response_content_validator.errors
            )
        )
        error_response = {
            'type':            'invalid_response_schema',
            'title':           'Invalid response schema',
            'error_status':    'Response content does not meet' +
                               'the OpenAPI Schema requirements',
            'status_code':     response.status_code,
            'url':             request_url,
            'text':            error_message,
            'parsed_response': parsed_response,
        }
        report_error(error_response)
        return error_response

    return {
        'type':            'success',
        'parsed_response': parsed_response
    }


def make_request(request_url: str, log_client_error=False):
    response = prepare_request(request_url, log_client_error)

    if response['type'] != 'success':
        return response
    else:
        request, openapi_request = itemgetter(
            'request',
            'openapi_request'
        )(response)

    return file_request(request, openapi_request, request_url)
