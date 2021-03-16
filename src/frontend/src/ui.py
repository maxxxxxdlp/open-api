from flask import render_template
from src.frontend.src import read_schema
import simplejson as json


def menu() -> str:
    """
    Render main screen
    Returns:
        str:
            main screen HTML
    """
    return render_template(
        'tags_menu.html',
        title='S^N',
        tags=read_schema.tags
    )


def tag(tag_name: str) -> str:
    """
    Render endpoints for a tag
    Args:
        tag_name(str): tag to render endpoints for

    Returns:
        str:
            tags screen HTML
    """
    return render_template(
        'routes_menu.html',
        title=tag_name,
        tag_name=tag_name,
        paths=read_schema.get_routes_for_tag(tag_name)
    )


def endpoint(tag_name: str, path_index: int) -> str:
    """
    Render UI for an endpoint
    Args:
        tag_name(str): name of the tag the endpoint belongs to
        path_index(int): index of the endpoint among tag's endpoints

    Returns:
        str:
            HTML for an endpoint UI

    """
    path_detailed_info = read_schema.get_data_for_route(tag_name, path_index)
    path_detailed_info_json = json.dumps(path_detailed_info).replace('`', '\`')
    return render_template(
        'endpoint.html',
        title=tag,
        tag_name=tag_name,
        path_detailed_info=path_detailed_info,
        path_detailed_info_json=path_detailed_info_json
    )
