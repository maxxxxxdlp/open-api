"""Utility functions for running the tests."""

import functools
import urllib
from dataclasses import dataclass
from typing import List, Tuple, Union


@dataclass
class ParameterData:
    """Parsed API endpoint's parameter."""

    name: str
    location: str
    required: Union[bool, None]
    examples: List[any]
    type: str
    default: Union[bool, None]


def validate_parameter_data(
    endpoint_name: str, parameter_data: ParameterData
) -> None:
    """
    Validate OpenAPI schema's `parameters` section of an entrypoint.

    Validate that the API schema has correct parameter properties
    specified.

    Args:
        endpoint_name (str): The name of the endpoint parameter belongs too
        parameter_data (ParameterData): Parsed API endpoint's parameter

    Returns:
        Union[str, None]:
            None if validation is successful.
            String 'continue' if parameter needs to be skipped

    Raises:
        AssertionError: on validation issue
    """
    signature = f"({endpoint_name} -> {parameter_data.name})"
    try:
        if (
            parameter_data.type != "boolean"
            and not parameter_data.examples
        ):
            print(
                f"Warning: Non-bool parameters should have examples "
                f"defined. Otherwise, example values would be auto generated "
                f"{signature}"
            )

        if (
            parameter_data.type == "boolean"
            and parameter_data.default is None
        ):
            raise AssertionError(
                "Bool parameter must have a default value"
            )

        if (
            parameter_data.default is not None
            and parameter_data.required
        ):
            raise AssertionError(
                "Parameter can be required or have a default value, "
                + "but not both"
            )

        if (
            parameter_data.default is None
            and parameter_data.required is None
        ):
            raise AssertionError(
                "Non-required parameters must have default value assigned"
            )

        if (
            not parameter_data.required
            and parameter_data.location == "path"
        ):
            raise AssertionError(
                "Parameters that are part of the path must be required"
            )

        if parameter_data.location not in ["path", "query"]:
            raise AssertionError(
                "Only parameters in path or query are supported for "
                + "validation!"
            )
    except AssertionError as e:
        raise AssertionError(
            f"{e} {signature}"
        )


def create_request_payload(
    endpoint_name: str,
    parameters: List[ParameterData],
    variation: List[any],
    base_url: str,
) -> Tuple[Tuple[str, str], str]:
    """Fill the parameters into the endpoint URL.

    Args:
        endpoint_name: the name of the endpoint
        parameters: list of parameters for the endpoint
        variation: list of values for each parameter
        base_url: base API url address

    Returns:
        (any,str):
            The payload object and the endpoint request URL with embedded
            parameters
    """
    return (
        variation[0],
        functools.reduce(
            lambda request_url, parameter: (
                request_url.replace(
                    "{%s}" % parameter[0].name,
                    urllib.parse.quote(str(parameter[1])),
                )
                if parameter[0].location == "path"
                else (
                    "%s%s=%s&"
                    % (
                        request_url,
                        parameter[0].name,
                        urllib.parse.quote(str(parameter[1])),
                    )
                    if parameter[1] != ""
                    else request_url
                )
            ),
            list(zip(parameters, variation))[1:],
            "{}{}?".format(base_url, endpoint_name),
        ),
    )
