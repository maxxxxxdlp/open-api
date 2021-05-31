"""Allow to test a chain of requests."""
import json
from typing import Any, Callable, List, Tuple, Union

from termcolor import colored

from open_api_tools.common.load_schema import Schema
from open_api_tools.test.test_endpoint import parse_parameters
from open_api_tools.test.utils import create_request_payload
from open_api_tools.validate.index import make_request


# FIXME: add support for changing the request object
# FIXME: test chain
def chain(
    schema: Schema,
    definition: List[Union[Tuple[str, str], Callable[[Any], Any]]],
):
    """Create a chain of requests.

    params:
        defintion:
            Chain defintion. More info in `README.md`
        open_api_schema:
    """

    response = None
    request = {"requestBody": None}

    base_url = schema.schema.servers[0].url

    for index, line in enumerate(definition):
        if type(line) is tuple:
            method, endpoint_name = line
            print(
                colored(f"[{index}/{len(definition)}]", "cyan")
                + " "
                + colored(
                    f"Fetching data from [{method}] {endpoint_name}",
                    "blue",
                )
            )

            parameters = parse_parameters(
                endpoint_name,
                schema.schema.paths[endpoint_name],
                method,
                False,
            )
            variation = [
                request[parameter.name]
                if parameter.name in request
                else None
                for parameter in parameters
            ]

            body, request_url = create_request_payload(
                endpoint_name, parameters, variation, base_url
            )

            response = make_request(
                request_url=request_url,
                method=method,
                body=body,
                schema=schema,
            )

            if response.type != "success":
                print(
                    colored(
                        json.dumps(
                            response._asdict(), indent=4, default=str
                        ),
                        "yellow",
                    )
                )
                return

            if response.type == "invalid_request_url":
                raise Exception(response.type)

            if "parsed_response" in response._asdict():
                response = response.parsed_response
        else:
            request = line(response)
            if not request:
                return
