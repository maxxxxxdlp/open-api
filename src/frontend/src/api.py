import json
from flask import render_template
from src.frontend.src.format_response import format_response
from src.automated_testing.openapi.index import make_request


def fetch_response(endpoint: str, request_url: str) -> str:
    """
    Fetches a response for an endpoint and formats the response
    Also, handles possible errors
    Args:
        endpoint(str): name of the endpoint
        request_url(str): request url to send a request too

    Returns:
        str:
            Formatted response or formatted error message
    """
    response = make_request(request_url)

    error = '' if response['type'] == 'success' else \
        render_template(
            'error_message.html',
            title=response['title'],
            message=response['error_status']
        )

    if response['type'] == 'invalid_request_url':
        return error

    if response['type'] == 'invalid_response_code' \
        or response['type'] == 'invalid_response_mime_type':
        return '<iframe class="error_iframe" srcdoc="%s"></iframe>' \
               % response['text'].replace('&', '&amp;').replace('"', '&quot;')

    # format the response in a human-friendly format
    return error + format_response(endpoint, response['parsed_response'])
