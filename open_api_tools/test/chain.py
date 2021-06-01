"""Allow to test a chain of requests."""
import json
from typing import Callable, List, Dict, Union

from dataclasses import dataclass
from termcolor import colored

from open_api_tools.common.load_schema import Schema
from open_api_tools.test.test_endpoint import parse_parameters
from open_api_tools.test.utils import create_request_payload
from open_api_tools.validate.index import make_request


@dataclass
class Request:
    """Chain's request defintion."""

    method: str
    endpoint: str
    parameters: Union[
        None,
        Dict[str,any], Callable[[any, List[any]],Dict[str,any]]
    ] = None


@dataclass
class Validate:
    """Chain's validator defintion."""

    validate: Callable[[any],bool]


def chain(
    schema: Schema,
    definition: List[Union[Request, Validate]],
    before_request_send: Union[Callable[[str, any],any],None] = None
):
    """Create a chain of requests.

    params:
        schema: A schema object
        defintion:
            Chain defintion. More info in `README.md`
        before_request_send:
            A pre-hook that allows to amend the request object
    """

    response = None
    request = {"requestBody": None}

    base_url = schema.schema.servers[0].url

    for index, line in enumerate(definition):
        if type(line) is Request:
            print(
                colored(f"[{index}/{len(definition)}] ", "cyan")
                + colored(
                    f"Fetching data from [{line.method}] {line.endpoint}",
                    "blue",
                )
            )

            if line.endpoint not in schema.schema.paths:
                raise Exception(
                    f"{line.endpoint} endpoint does not exist in your OpenAPI "
                    f"schema. Make sure to provide a URL without parameters "
                    f"and with a trailing '/' if it is present in the "
                    f"definition"
                )

            parameters = parse_parameters(
                endpoint_name=line.endpoint,
                endpoint_data=schema.schema.paths[line.endpoint],
                method=line.method.lower(),
                generate_examples=False,
            )

            if type(line.parameters) is dict:
                request = line.parameters
            elif callable(line.parameters):
                request = line.parameters(parameters, response, request)

            variation = [
                request[parameter.name]
                if parameter.name in request
                else None
                for parameter in parameters
            ]

            body, request_url = create_request_payload(
                line.endpoint, parameters, variation, base_url
            )

            response = make_request(
                request_url=request_url,
                endpoint_name=line.endpoint,
                method=line.method.lower(),
                body=body,
                schema=schema,
                before_request_send= lambda request:
                    before_request_send(line.endpoint, request)
            )

            if response.type != "success":
                raise Exception(json.dumps(
                    response._asdict() \
                        if hasattr(response,'_asdict') \
                        else response,
                    indent=4,
                    default=str
                ))

            response = response.response

        elif type(line) is Validate:
            print(
                colored(f"[{index}/{len(definition)}] ", "cyan")
                + colored(
                    f"Validating the response",
                    "blue",
                )
            )
            if not line.validate(response):
                return
        else:
            raise Exception(
                f'Invalid chain line detected at index {index}:"'
                f' {str(line)}'
            )
