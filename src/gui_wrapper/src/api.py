import requests
from src.utils import report_error
import json

def fetch_response(request_url: str) -> str:
	request = requests.get(request_url)
	if request.status_code != 200:
		report_error(json.dumps({
			'status_code': request.status_code,
			'url': request_url,
			'text': request.text,
		}, indent=4))
	return request.text
