from typing import Dict, List, Union, Callable
from termcolor import colored
import string
import random
import itertools
import json

from open_api_tools.common.load_schema import Schema
from open_api_tools.test.utils import (
    ParameterData,
    create_request_payload,
    validate_parameter_data,
)
from open_api_tools.validate.index import ErrorMessage, make_request


class InlineClass(object):
    def __init__(self, dict):
        self.__dict__ = dict


def parse_parameters(
    endpoint_name: str,
    endpoint_data,
    method: str,
    generate_examples: bool,
    parameter_values_generator: Union[
        None, Callable[[str, Dict[str, any], List[any]], List[any]]
    ] = None,
):
    """Parse endpoint's parameters.

    Parse parameters, validate them and generate test values for each.
    """
    parameters: List[ParameterData] = [
        InlineClass(
            {
                "name": "requestData",
                "examples": parameter_values_generator(
                    endpoint_name, {"name": "requestBody"}, [None]
                )
                if parameter_values_generator
                else [None],
            }
        )
    ]

    for parameter in getattr(endpoint_data, method).parameters:
        parameter_data = ParameterData(
            parameter.name,
            parameter.in_,
            parameter.required,
            [value["value"] for value in parameter.examples.values()]
            if parameter.examples
            else [],
            parameter.schema.type,
            parameter.schema.default,
        )

        if (
            validate_parameter_data(endpoint_name, parameter_data)
            == "continue"
        ):
            continue

        if generate_examples and not parameter.examples:
            letters = None
            length = 8
            if parameter.schema.type == "string":
                letters = string.ascii_letters
                length = 8
            elif parameter.schema.type == "integer":
                letters = string.digits
                length = 2

            if letters:
                parameter_data.examples = [
                    "".join(random.choice(letters) for _i in range(10))
                    for _ii in range(length)
                ]

        if parameter_data.type == "boolean":
            parameter_data.examples = [True, False]

        if (
            not parameter_data.required
            and "" not in parameter_data.examples
        ):
            parameter_data.examples.append("")

        if parameter_values_generator:
            parameter_data.examples = parameter_values_generator(
                endpoint_name,
                parameter.raw_element,
                parameter_data.examples,
            )

        parameters.append(parameter_data)

    return parameters


def test_endpoint(
    endpoint_name: str,
    method: str,
    base_url: str,
    should_continue_on_fail: Callable[[], bool],
    schema: Schema,
    max_urls_per_endpoint: int,
    error_callback: Callable[[ErrorMessage], None],
    parameter_constraints: Union[
        None, Dict[str, Callable[[bool, str, Dict[str, any]], bool]]
    ] = None,
    parameter_values_generator: Union[
        None, Callable[[str, Dict[str, any], List[any]], List[any]]
    ] = None,
):
    print(colored("Testing [{}] `{}`".format(method, endpoint_name), "red"))

    parameters = parse_parameters(
        endpoint_name,
        schema.schema.paths[endpoint_name],
        method,
        True,
        parameter_values_generator,
    )

    parameter_names = list(map(lambda p: p.name, parameters))

    # creating url variations based on parameters
    parameter_variations = list(
        itertools.product(*map(lambda p: p.examples, parameters))
    )

    payloads = list(
        map(
            lambda variation: create_request_payload(
                endpoint_name, parameters, variation, base_url
            ),
            parameter_variations,
        )
    )

    print(
        "Created %d test URLS for the `%s` endpoint"
        % (len(payloads), endpoint_name)
    )

    # if more than `max_urls_per_endpoint` urls, take a random sample
    if len(payloads) > max_urls_per_endpoint:
        payloads, parameter_variations = zip(
            *random.sample(
                list(zip(payloads, parameter_variations)),
                max_urls_per_endpoint,
            )
        )
        print(
            "Downsizing the sample of test URLS to %d"
            % max_urls_per_endpoint
        )

    # testing all url variations for validness
    # fetching all the responses
    # validating responses against schema
    responses: Dict[int, object] = {}
    for index, payload in enumerate(payloads):

        body, request_url = payload

        print(
            "%s %s"
            % (
                colored("[%d/%d]" % (index, len(payloads)), "cyan"),
                colored(
                    "Fetching response from %s" % request_url,
                    "blue",
                ),
            )
        )

        response = make_request(
            request_url, method, body, error_callback, schema
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
            if not should_continue_on_fail():
                return

        if response.type == "invalid_request_url":
            raise Exception(response.type)

        if "parsed_response" in response._asdict():
            responses[index] = response.parsed_response

    # running tests though constraints
    defined_constraints = {
        parameter_name: constraint_function
        for parameter_name, constraint_function in parameter_constraints.items()
        if parameter_name in parameter_names
    }
    if defined_constraints:
        for request_index, response_data in responses.items():
            for (
                parameter_name,
                constraint_function,
            ) in defined_constraints.items():

                parameter_value = parameter_variations[request_index][
                    parameter_names.index(parameter_name)
                ]
                if parameter_value == "":
                    parameter_value = parameters[
                        parameter_names.index(parameter_name)
                    ].default

                if not constraint_function(
                    parameter_value, endpoint_name, response_data
                ):
                    error_message = ErrorMessage(
                        type="failed_test_constraint",
                        title="Testing constraint failed",
                        error_status=f"Constraint on the {endpoint_name} based "
                        + f"on a parameter {parameter_name} failed",
                        url=payloads[request_index][1],
                        extra={"parsed_response": response_data},
                    )
                    error_callback(error_message)
                    print(
                        colored(
                            json.dumps(
                                error_message, indent=4, default=str
                            ),
                            "yellow",
                        )
                    )
