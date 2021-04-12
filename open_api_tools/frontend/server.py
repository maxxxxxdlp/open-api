from flask import Flask, request
from open_api_tools.frontend.common.load_schema import load_schema
from open_api_tools.frontend.src import api, ui
import os


if "SCHEMA_LOCATION" not in os.environ:
    raise RuntimeError(
        "Please specify the location of the schema via"
        + "the `SCHEMA_LOCATION` environmental variable"
    )

schema, core_spec = load_schema(os.environ["SCHEMA_LOCATION"])

app = Flask(__name__)


@app.route("/")
def index() -> str:
    return ui.menu(schema)


@app.route("/routes/<string:tag>/")
def routes(tag: str) -> str:
    return ui.tag(schema, tag)


@app.route("/endpoint/<string:tag>/<int:route>/")
def endpoint(tag: str, route: int) -> str:
    return ui.endpoint(schema, tag, route - 1)


@app.route("/api/fetch_response/", methods=["POST"])
def fetch_response() -> str:
    content = request.json
    return api.fetch_response(
        core_spec, content["endpoint"], content["requestUrl"]
    )
