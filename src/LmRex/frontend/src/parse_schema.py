from typing import Dict, List, NamedTuple, Union
from openapi3 import OpenAPI
import yaml
from LmRex.config import frontend_config as settings

with open(settings.OPEN_API_LOCATION) as file:
    spec = yaml.safe_load(file.read())

api = OpenAPI(spec)

tags = [[tag.name, tag.description] for tag in api.tags]


class RouteInfo(NamedTuple):
    """Short description of an API Endpoint"""
    path: str
    summary: str
    description: str


def get_routes_for_tag(tag: str) -> List[RouteInfo]:
    """
    Fetches a list of routes available for a particular tag
    Args:
        tag(str): tag to fetch routes for

    Returns:
        List[RouteInfo]:
            list of routes
    """
    return [
        RouteInfo(path, path_data.get.summary, path_data.get.description)
        for path, path_data in api.paths.items() if tag in path_data.get.tags
    ]


class RouteParameter(NamedTuple):
    """API Endpoint parameter"""
    name: str
    description: str
    required: bool
    default: Union[str, bool, int]
    examples: Dict[str, str]
    type: str
    location: str


class RouteDetailedInfo(NamedTuple):
    """API endpoint"""
    path: str
    server: str
    summary: str
    description: str
    parameters: List[RouteParameter]


def get_data_for_route(tag: str, route_index: int) -> RouteDetailedInfo:
    """
    Fetches the data needed to display the API endpoint
    Args:
        tag(str): name of the current tag
        route_index(int): index of a route among the routes for a tag

    Returns:

    """
    route: RouteInfo = get_routes_for_tag(tag)[route_index]
    return RouteDetailedInfo(
        route.path,
        api.servers[0].url,
        route.summary,
        route.description,
        [
            RouteParameter(
                parameter.name,
                parameter.description,
                parameter.required,
                parameter.schema.default,
                {
                    name: list(value.values())[0]
                    for name, value in parameter.examples.items()
                } if parameter.examples
                else {
                    parameter.example: parameter.example
                } if parameter.example
                else { },
                parameter.schema.type,
                parameter.in_,
            ) for parameter in api.paths[route.path].get.parameters
        ],
    )
