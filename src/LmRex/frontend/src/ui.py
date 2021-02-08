from LmRex.frontend.src import parse_schema
from LmRex.frontend.src import templates
import simplejson as json

tags_menu = templates.load('tags_menu.html')
routes_menu = templates.load('routes_menu.html')
endpoint_template = templates.load('endpoint.html')


def menu() -> str:
    return tags_menu(tags=parse_schema.tags)


def tag(tag_name: str) -> str:
    return routes_menu(tag_name=tag_name, paths=parse_schema.get_routes_for_tag(tag_name))


def endpoint(tag_name: str, path_index: int) -> str:
    path_detailed_info = parse_schema.get_data_for_route(tag_name, path_index)
    path_detailed_info_json = json.dumps(path_detailed_info).replace('`', '\`')
    return endpoint_template(
        tag_name=tag_name,
        path_detailed_info=path_detailed_info,
        path_detailed_info_json=path_detailed_info_json
    )
