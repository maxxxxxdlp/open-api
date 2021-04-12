from flask import render_template

from open_api_tools.frontend.src.format_response import format_response
from open_api_tools.validate.index import make_request


def fetch_response(core_spec, endpoint: str, request_url: str) -> str:
    """
    Fetches a response for an endpoint and formats the response
    Also, handles possible errors
    Args:
        core_spec: OpenAPI spec
        endpoint(str): name of the endpoint
        request_url(str): request url to send a request too

    Returns:
        str:
            Formatted response or formatted error message
    """
    response = make_request(
        request_url,
        lambda x: x,
        core_spec,
    )

    error = (
        ""
        if response.type == "success"
        else render_template(
            "error_message.html",
            title=response.title,
            message=response.error_status,
        )
    )

    if response.type == "invalid_request_url":
        return error

    if (
        response.type == "invalid_response_code"
        or response.type == "invalid_response_mime_type"
    ):
        return (
            '<iframe class="error_iframe" srcdoc="%s"></iframe>'
            % response.text.replace("&", "&amp;").replace('"', "&quot;")
        )

    if response.type == "invalid_response_schema":
        parsed_response = response.extra["parsed_response"]
    else:
        parsed_response = response.parsed_response

    # format the response in a human-friendly format
    return error + format_response(endpoint, parsed_response)
