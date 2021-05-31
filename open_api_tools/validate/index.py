"""A validator for request/response objects powered by OpenAPI schema."""

import json
import urllib.parse as urlparse
from json import JSONDecodeError
from typing import Callable, Dict, Tuple, Union
from dataclasses import dataclass
from urllib.parse import parse_qs
from openapi_core.contrib.requests import (
    RequestsOpenAPIRequest,
    RequestsOpenAPIResponseFactory,
)
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import (
    ResponseValidator,
)
from requests import Request, Session

from open_api_tools.common.load_schema import Schema

session = Session()


@dataclass
class ErrorMessage:
    """An error returned by the validator."""

    type: str
    title: str
    error_status: str
    url: str
    extra: Dict


@dataclass
class PreparedRequest:
    """A successful prepared request."""

    type: str
    request: object
    openapi_request: object


def prepare_request(
    request_url: str,
    method: str,
    body: Union[Tuple[str, str], None],
    schema: Schema,
    after_error_occurred: Callable[[ErrorMessage], None] = None,
    before_request_send: Union[Callable[[any],any],None] = None
) -> Union[PreparedRequest, ErrorMessage]:
    """Prepare request and validate the request URL.

    Args:
        request_url (str): request URL
        method (str): HTTP method name
        body (Union[Dict, None]: payload to send along with the request
        schema (Schema): OpenAPI schema
        after_error_occurred: function to call in case of an error
        before_request_send: A pre-hook that allows to amend the request object

    Returns:
        object: Prepared request or error message
    """

    if after_error_occurred is None:
        after_error_occurred = lambda _error: None

    if before_request_send is None:
        before_request_send = lambda request: request

    request_validator = RequestValidator(schema.open_api_core)
    parsed_url = urlparse.urlparse(request_url)
    base_url = request_url.split("?")[0]
    query_params_dict = parse_qs(parsed_url.query)

    if body is None:
        headers = {}
        request_body = ''
    else:
        mime_type, request_body = body
        headers = { 'Content-type': mime_type }

    request = Request(
        method=method,
        url=base_url,
        params=query_params_dict,
        data=request_body,
        headers=headers
    )
    if before_request_send:
        request = before_request_send(request)
    openapi_request = RequestsOpenAPIRequest(request)
    request_url_validator = request_validator.validate(openapi_request)

    if request_url_validator.errors:
        error_message = request_url_validator.errors
        error_response = ErrorMessage(
            type="invalid_request_url",
            title="Invalid Request URL",
            error_status=(
                "Request URL does not meet the OpenAPI Schema Requirements"
            ),
            url=request_url,
            extra={
                "text": error_message,
            },
        )
        after_error_occurred(error_response)
        return error_response

    return PreparedRequest(
        type="success",
        request=request,
        openapi_request=openapi_request,
    )


@dataclass
class FiledRequest:
    """A successful filed request with a response."""

    type: str
    parsed_response: object
    raw_response: object


def file_request(
    request,
    openapi_request,
    request_url: str,
    schema: Schema,
    after_error_occurred: Callable[[ErrorMessage], None] = None,
) -> Union[ErrorMessage, FiledRequest]:
    """
    Send a prepared request and validate the response.

    Args:
        request: request object
        openapi_request: openapi request object
        request_url (str): request url
        after_error_occurred: function to call in case of an error
        schema (Schema): OpenAPI schema

    Returns:
        Request response or error message
    """

    if after_error_occurred is None:
        after_error_occurred = lambda _error: None

    response_validator = ResponseValidator(schema.open_api_core)
    prepared_request = request.prepare()
    response = session.send(prepared_request)

    # FIXME:
    # test response code is in schema
    # test response type in in response code
    # validate the schema using jsonschema
    # delete the lines below:


    # make sure that the server did not return an error
    if response.status_code != 200:
        error_response = ErrorMessage(
            type="invalid_response_code",
            title="Invalid Response",
            error_status="Response status code indicates an error has "
            + "occurred",
            url=request_url,
            extra={
                "status_code": response.status_code,
                "text": response.text,
            },
        )
        after_error_occurred(error_response)
        return error_response

    # make sure the response is a valid JSON object
    try:
        parsed_response = json.loads(response.text)
    except JSONDecodeError:
        error_response = ErrorMessage(
            type="invalid_response_mime_type",
            title="Invalid response",
            error_status="Unable to parse JSON response",
            url=request_url,
            extra={
                "status_code": response.status_code,
                "text": response.text,
            },
        )
        after_error_occurred(error_response)
        return error_response

    # validate the response against the schema
    formatted_response = RequestsOpenAPIResponseFactory.create(response)
    response_content_validator = response_validator.validate(
        openapi_request, formatted_response
    )

    if response_content_validator.errors:
        error_message = list(
            map(
                lambda e: str(e),
                response_content_validator.errors,
            )
        )
        error_response = ErrorMessage(
            type="invalid_response_schema",
            title="Invalid response schema",
            error_status="Response content does not meet the OpenAPI "
            + "Schema requirements",
            url=request_url,
            extra={
                "text": error_message,
                "parsed_response": parsed_response,
            },
        )
        after_error_occurred(error_response)
        return error_response

    return FiledRequest(
        type="success",
        parsed_response=parsed_response,
        raw_response=response
    )


def make_request(
    request_url: str,
    method: str,
    body: Union[Tuple[str, str], None],
    schema: Schema,
    after_error_occurred: Callable[[ErrorMessage], None] = None,
    before_request_send: Union[Callable[[any],any],None] = None
):
    """
    Combine `prepared_request` and `file_request`.

    Prepare a request and send it, while running validation on each
    step.

    Args:
        request_url (str): request error
        method (str): HTTP method name
        body (Union[Dict, None]: payload to send along with the request
        schema (Schema): OpenAPI schema
        after_error_occurred: function to call in case of an error
        before_request_send: A pre-hook that allows to amend the request object

    Returns:
        Request response or error message
    """

    response = prepare_request(
        request_url=request_url,
        method=method,
        body=body,
        schema=schema,
        after_error_occurred=after_error_occurred,
        before_request_send=before_request_send
    )

    if response.type != "success":
        return response

    return file_request(
        request=response.request,
        openapi_request=response.openapi_request,
        request_url=request_url,
        schema=schema,
        after_error_occurred=after_error_occurred,
    )
