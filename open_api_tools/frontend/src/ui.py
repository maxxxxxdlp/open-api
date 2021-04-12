"""Render templates for common UI components."""

import simplejson as json
from flask import render_template

from open_api_tools.frontend.src import read_schema


def menu(schema) -> str:
    """
    Render main screen.

    Args:
        schema: OpenAPI schema

    Returns:
        str:
            main screen HTML
    """
    tags = [[tag.name, tag.description] for tag in schema.tags]
    return render_template("tags_menu.html", title="S^N", tags=tags)


def tag(schema, tag_name: str) -> str:
    """
    Render endpoints for a tag.

    Args:
        schema: OpenAPI schema
        tag_name(str): tag to render endpoints for

    Returns:
        str:
            tags screen HTML
    """
    return render_template(
        "routes_menu.html",
        title=tag_name,
        tag_name=tag_name,
        paths=read_schema.get_routes_for_tag(schema, tag_name),
    )


def endpoint(schema, tag_name: str, path_index: int) -> str:
    """
    Render UI for an endpoint.

    Args:
        schema: OpenAPI schema
        tag_name(str): name of the tag the endpoint belongs to
        path_index(int): index of the endpoint among tag's endpoints

    Returns:
        str:
            HTML for an endpoint UI

    """
    path_detailed_info = read_schema.get_data_for_route(
        schema, tag_name, path_index
    )
    path_detailed_info_json = json.dumps(path_detailed_info).replace(
        "`", "\\`"
    )
    return render_template(
        "endpoint.html",
        title=tag,
        tag_name=tag_name,
        path_detailed_info=path_detailed_info,
        path_detailed_info_json=path_detailed_info_json,
    )
