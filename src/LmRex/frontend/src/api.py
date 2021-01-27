import json

from LmRex.frontend.src.format_response import format_response
from LmRex.automated_testing.openapi.index import make_request


def fetch_response(endpoint: str, request_url: str) -> str:

	response = make_request(request_url)

	if response['type'] == 'invalid_request_url' \
			or response['type'] == 'invalid_response_schema'\
			or response['type'] == 'invalid_response_mime_type':
		return '<pre>%s</pre>' % json.dumps(response, indent=4, default=str)

	if response['type'] == 'invalid_response_code':
		return '<iframe class="error_iframe" srcdoc="%s"></iframe>' \
			% response['text'].replace('&', '&amp;').replace('"', '&quot;')

	# format the response in a human-friendly format
	return format_response(endpoint, response['parsed_response'])
