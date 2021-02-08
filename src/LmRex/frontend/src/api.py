import json
from LmRex.frontend.src.format_response import format_response
from LmRex.automated_testing.openapi.index import make_request
from LmRex.frontend.src import templates

error_message = templates.load('error_message.html')


def fetch_response(endpoint: str, request_url: str) -> str:
    response = make_request(request_url)

    error = '' if response['type'] == 'success' else \
        error_message(title=response['title'], message=response['error_status'])

    if response['type'] == 'invalid_request_url':
        return error

    if response['type'] == 'invalid_response_code' \
        or response['type'] == 'invalid_response_mime_type':
        return '<iframe class="error_iframe" srcdoc="%s"></iframe>' \
               % response['text'].replace('&', '&amp;').replace('"', '&quot;')

    # format the response in a human-friendly format
    return error + format_response(endpoint, response['parsed_response'])
