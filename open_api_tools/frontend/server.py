"""The entrypoint for the OpenAPI schema UI."""

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
    """Render the main page. Lists available tags.

    Returns:
        str: HTML for the main page
    """
    return ui.menu(schema)


@app.route("/routes/<string:tag>/")
def routes(tag: str) -> str:
    """Render the list of entrypoints by tag.

    Args:
        tag (str): the name of the tag

    Returns:
        str: HTML for the `routes` page
    """
    return ui.tag(schema, tag)


@app.route("/endpoint/<string:tag>/<int:route>/")
def endpoint(tag: str, route: int) -> str:
    """Render detailed information about a single entrypoint.

    Args:
        tag (Str): the name of the tag
        route (int): the index of the route amongs the tag's routes

    Returns:
        str: HTML for the `entrypoint` page
    """
    return ui.endpoint(schema, tag, route - 1)


@app.route("/api/fetch_response/", methods=["POST"])
def fetch_response() -> str:
    """Send a request to the server and parses the response.

    The request should contains a json object with the name of the
    entypoint (`entrypoint`) and the request URL (`requestUrl`)

    Returns:
        str:
            HTML for the parsed returned response or an error message
    """
    content = request.json
    return api.fetch_response(
        core_spec, content["endpoint"], content["requestUrl"]
    )
