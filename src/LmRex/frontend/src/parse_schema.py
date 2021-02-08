from typing import Dict, List, NamedTuple, Union
from openapi3 import OpenAPI
import yaml
from LmRex.config import frontend_config as settings

with open(settings.OPEN_API_LOCATION) as file:
    spec = yaml.safe_load(file.read())

api = OpenAPI(spec)

tags = [[tag.name, tag.description] for tag in api.tags]


class RouteInfo(NamedTuple):
    path: str
    summary: str
    description: str


def get_routes_for_tag(tag: str) -> List[RouteInfo]:
    return [
        RouteInfo(path, path_data.get.summary, path_data.get.description)
        for path, path_data in api.paths.items() if tag in path_data.get.tags
    ]


class RouteParameter(NamedTuple):
    name: str
    description: str
    required: bool
    default: Union[str, bool, int]
    examples: Dict[str, str]
    type: str
    location: str


class RouteDetailedInfo(NamedTuple):
    path: str
    server: str
    summary: str
    description: str
    parameters: List[RouteParameter]


def get_data_for_route(tag: str, route_index: int) -> RouteDetailedInfo:
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
                else { parameter.example: parameter.example } if parameter.example
                else { },
                parameter.schema.type,
                parameter.in_,
            ) for parameter in api.paths[route.path].get.parameters
        ],
    )


"""

# call an operation that requires authentication
linodes = api.call_getLinodeInstances()


linode = api.call_getLinodeInstance(parameters={ "linodeId": 123 })

# the models returns are all of the same (generated) type
print(type(linode))  # openapi.schemas.Linode
type(linode) == type(linodes.data[0])  # True

# call an operation with a request body
new_linode = api.call_createLinodeInstance(data={ "region": "us-east", "type": "g6-standard-2" })

# the returned models is still of the correct type
type(new_linode) == type(linode)  # True
"""
