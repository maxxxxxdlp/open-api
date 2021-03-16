from flask import Flask, render_template
from src.frontend.src import ui
from src.frontend.src import api


app = Flask(__name__)


@app.route('/')
def index() -> str:
    return render_template('index.html',title='S^N', content=ui.menu())


@app.route('/routes/<str:tag>/')
def routes(tag: str) -> str:
    return render_template('index.html',title=tag, content=ui.tag(tag))


@app.route('/endpoint/<str:tag>/<int:route>/')
def endpoint(tag: str, route: int) -> str:
    return render_template(
        'index.html',
        title=tag,
        content=ui.endpoint(tag, route - 1)
    )

@app.route('/api/fetch_response/<str:endpoint>/<str:url>')
def fetch_response(endpoint: str, url: str) -> str:
    return api.fetch_response(endpoint, url)

