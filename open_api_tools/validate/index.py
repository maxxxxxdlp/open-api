# -*- coding: utf-8 -*-
"""A validator for request/response objects powered by OpenAPI schema."""

import json
import urllib.parse as urlparse
from typing import Callable, Dict, Tuple, Union
from dataclasses import dataclass
from urllib.parse import parse_qs
from openapi_core.contrib.requests import (
    RequestsOpenAPIRequest,
)
from openapi_core.validation.request.validators import RequestValidator
from requests import Request, Session

from open_api_tools.common.load_schema import Schema
from open_api_tools.common.transform_schema import validate_object

session = Session()


@dataclass
class ErrorMessage:
    """An error returned by the validator."""

    type: str
    title: str
    error_status: str
    url: str
    extra: Dict = None


@dataclass
class PreparedRequest:
    """A successful prepared request."""

    type: str
    request: object
    openapi_request: object


def prepare_request(
    schema: Schema,
    request_url: str,
    endpoint_name: str,
    method: str,
    body: Union[Tuple[str, str], None],
    after_error_occurred: Callable[[ErrorMessage], None] = None,
    before_request_send: Union[Callable[[any], any], None] = None,
) -> Union[PreparedRequest, ErrorMessage]:
    """Prepare request and validate the request URL.

    Args:
        schema (Schema): OpenAPI schema
        request_url (str): request URL
        endpoint_name (str): endpoint name
        method (str): HTTP method name
        body: payload to send along with the request
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
        mime_type = ""
        request_body = ""
    else:
        mime_type, request_body = body
        headers = {"Content-type": mime_type}

    endpoint_schema = getattr(
        schema.schema.paths[endpoint_name], method
    )
    request_body_schema = endpoint_schema.requestBody
    endpoint_schema.requestBody = None

    if request_body_schema is not None:
        if request_body_schema.required and request_body == "":
            error_response = ErrorMessage(
                type="invalid_request",
                title="Invalid Request",
                error_status=("Required requestBody is missing"),
                url=request_url,
                extra={"body": body, "mime_type": mime_type},
            )
            after_error_occurred(error_response)
            return error_response

        accepted_content_types = list(
            request_body_schema.content.raw_element.keys()
        )
        if mime_type not in accepted_content_types:
            error_response = ErrorMessage(
                type="invalid_request",
                title="Invalid Request",
                error_status=(
                    f"Request body's content type "
                    f"({mime_type}) is not in "
                    f"the list of accepted content types "
                    f"({accepted_content_types})"
                ),
                url=request_url,
                extra={"body": body, "mime_type": mime_type},
            )
            after_error_occurred(error_response)
            return error_response

        try:
            validate_object(
                getattr(
                    request_body_schema.content.raw_element, mime_type
                ).schema,
                schema.schema.components.raw_element,
                headers,
                mime_type,
            )
        except Exception as error:
            error_response = ErrorMessage(
                type="invalid_request",
                title="Invalid Request",
                error_status=str(error),
                url=request_url,
                extra={"error_object": json.dumps(error, default=str)},
            )
            after_error_occurred(error_response)
            return error_response

    request = Request(
        method=method,
        url=base_url,
        params=query_params_dict,
        data=request_body,
        headers=headers,
    )
    if before_request_send:
        request = before_request_send(request)
    openapi_request = RequestsOpenAPIRequest(request)
    request_url_validator = request_validator.validate(openapi_request)
    endpoint_schema.requestBody = request_body

    if request_url_validator.errors:
        error_message = request_url_validator.errors
        error_response = ErrorMessage(
            type="invalid_request",
            title="Invalid Request",
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
    response: object


def file_request(
    schema: Schema,
    request_url: str,
    endpoint_name: str,
    request,
    after_error_occurred: Callable[[ErrorMessage], None] = None,
) -> Union[ErrorMessage, FiledRequest]:
    """
    Send a prepared request and validate the response.

    Args:
        schema (Schema): OpenAPI schema
        request_url (str): request url
        endpoint_name (str): endpoint name
        request: request object
        openapi_request: openapi request object
        after_error_occurred: function to call in case of an error

    Returns:
        Request response or error message
    """

    method = request.method.lower()

    if after_error_occurred is None:
        after_error_occurred = lambda _error: None

    prepared_request = request.prepare()
    response = session.send(prepared_request)

    # make sure that the server did not return an error
    endpoint_schema = getattr(
        schema.schema.paths[endpoint_name], method
    )

    response_code = str(response.status_code)
    if response_code not in endpoint_schema.responses:
        error_response = ErrorMessage(
            type="invalid_response",
            title="Invalid Request",
            error_status=(
                f"Response code ({response_code}) is invalid"
            ),
            url=request_url,
        )
        after_error_occurred(error_response)
        return error_response

    response_schema = endpoint_schema.responses[response_code]

    if response_code == "204":
        return FiledRequest(type="success", response=response)

    elif not hasattr(response_schema, "content"):
        error_response = ErrorMessage(
            type="invalid_response",
            title="Invalid Request",
            error_status=(
                f"No response schema is defined for "
                f"{response_code} response code."
            ),
            url=request_url,
        )
        after_error_occurred(error_response)
        return error_response

    response_types = list(response_schema.content.keys())

    content_type = response.headers["Content-Type"]

    if content_type not in response_types:
        error_response = ErrorMessage(
            type="invalid_response",
            title="Invalid Request",
            error_status=(
                f"The response's content type ({content_type}) "
                f"is not in the list of defined content types "
                f"({', '.join(response_types)})."
            ),
            url=request_url,
            extra={
                "response_content": json.dumps(
                    response, indent=4, default=str
                )
            },
        )
        after_error_occurred(error_response)
        return error_response

    # Use JSON Schema to validate a JSON response
    openapi_response_schema = response_schema.content[
        content_type
    ].raw_element["schema"]
    try:
        validate_object(
            openapi_response_schema,
            schema.schema.components.raw_element,
            response.content,
            content_type,
        )
    except Exception as error:
        error_response = ErrorMessage(
            type="invalid_response",
            title="Invalid response",
            error_status="Response content does not meet the OpenAPI "
            + "Schema requirements",
            url=request_url,
            extra={
                "error": json.dumps(error, indent=4, default=str),
                "response": json.dumps(response, indent=4, default=str),
                "response_content": response.content,
            },
        )
        after_error_occurred(error_response)
        return error_response

    return FiledRequest(type="success", response=response)


def make_request(
    schema: Schema,
    request_url: str,
    endpoint_name: str,
    method: str,
    body: Union[Tuple[str, str], None],
    after_error_occurred: Callable[[ErrorMessage], None] = None,
    before_request_send: Union[Callable[[any], any], None] = None,
):
    """
    Combine `prepared_request` and `file_request`.

    Prepare a request and send it, while running validation on each
    step.

    Args:
        schema (Schema): OpenAPI schema
        request_url (str): full request url
        endpoint_name (str): endpoint name
        method (str): HTTP method name
        body (Union[Dict, None]: payload to send along with the request
        after_error_occurred: function to call in case of an error
        before_request_send: A pre-hook that allows to amend the request object

    Returns:
        Request response or error message
    """

    response = prepare_request(
        schema=schema,
        request_url=request_url,
        endpoint_name=endpoint_name,
        method=method,
        body=body,
        after_error_occurred=after_error_occurred,
        before_request_send=before_request_send,
    )

    if response.type != "success":
        return response

    return file_request(
        schema=schema,
        request=response.request,
        endpoint_name=endpoint_name,
        request_url=request_url,
        after_error_occurred=after_error_occurred,
    )
