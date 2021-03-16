import json
import urllib.parse as urlparse
from json import JSONDecodeError
from operator import itemgetter
from urllib.parse import parse_qs
from src.common.report_error import report_error
from openapi_core import create_spec
from openapi_core.contrib.requests import RequestsOpenAPIRequest, \
  RequestsOpenAPIResponseFactory
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from requests import Request, Session
from src.common.parse_schema import spec as yaml_schema


# convert schema
serializable_spec = json.loads(json.dumps(yaml_schema, default=str))
spec = create_spec(serializable_spec)

# initialize validators
request_validator = RequestValidator(spec)
response_validator = ResponseValidator(spec)
session = Session()


def prepare_request(request_url: str, log_errors: bool = False):
  """
  Prepare request and validate the request URL
  Args:
      request_url (str): request URL
      log_errors (bool): whether to log errors to the `error_logs` folder

  Returns:
      object: Prepared request or error message

  """
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
  """
  Send a prepared request and validate the response
  Args:
      request: request object
      openapi_request: openapi request object
      request_url (str): request url

  Returns:
      Request response or error message

  """
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
  """
  Prepares a request and sends it, while running validation on each step
  Args:
      request_url (str): request error
      log_client_error (boolean):
          whether to log request preparation error messages

  Returns:
      Request response or error message

  """
  response = prepare_request(request_url, log_client_error)

  if response['type'] != 'success':
    return response
  else:
    request, openapi_request = itemgetter(
      'request',
      'openapi_request'
    )(response)

  return file_request(request, openapi_request, request_url)
