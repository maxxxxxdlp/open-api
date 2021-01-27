from json import JSONDecodeError

import requests
from src.utils import report_error
import json
from src.format_response import format_response

def fetch_response(endpoint:str, request_url: str) -> str:
	request = requests.get(request_url)

	if request.status_code != 200:
		report_error({
			'error_status': 'Response status code is not 200',
			'status_code': request.status_code,
			'url': request_url,
			'text': request.text,
		})
		return '<iframe class="error_iframe" srcdoc="%s"></iframe>'\
			% request.text.replace('&','&amp;').replace('"','&quot;')

	try:
		response = json.loads(request.text)
	except JSONDecodeError:
		report_error({
			'error_status': 'Failure parsing JSON response',
			'status_code': request.status_code,
			'url':         request_url,
			'text':        request.text,
		})
		return request.text

	return format_response(endpoint, response)