from flask import Flask, request
from open_api_tools.frontend.src import api, ui

app = Flask(__name__)


@app.route('/')
def index() -> str:
    return ui.menu()


@app.route('/routes/<string:tag>/')
def routes(tag: str) -> str:
    return ui.tag(tag)


@app.route('/endpoint/<string:tag>/<int:route>/')
def endpoint(tag: str, route: int) -> str:
    return ui.endpoint(tag, route - 1)


@app.route(
    '/api/fetch_response/',
    methods=['POST']
)
def fetch_response() -> str:
    content = request.json
    return api.fetch_response(content['endpoint'], content['requestUrl'])
