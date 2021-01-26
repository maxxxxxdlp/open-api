import requests


def fetch_response(request_url: str) -> str:
	request = requests.get(request_url)
	return request.text
