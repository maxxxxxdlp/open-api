# -*- coding: utf-8 -*-
"""Run a comprehensive test on all defined endpoints."""

from typing import Dict, List, Union, Callable
from termcolor import colored

from open_api_tools.common.load_schema import Schema
from open_api_tools.validate.index import ErrorMessage
from open_api_tools.test.test_endpoint import test_endpoint


def full_test(
    schema: Schema,
    max_urls_per_endpoint: int = 50,
    failed_request_limit: int = 100,
    methods_to_test=None,
    parameter_constraints: Union[
        None, Dict[str, Callable[[bool, str, Dict[str, any]], bool]]
    ] = None,
    after_error_occurred: Callable[[ErrorMessage], None] = None,
    after_examples_generated: Union[
        None, Callable[[str, Dict[str, any], List[any]], List[any]]
    ] = None,
    before_request_send: Union[Callable[[str, any], any], None] = None,
) -> None:
    """Run a comprehensive test on all API endpoints.

    Args:
        schema:
            The schema object
        max_urls_per_endpoint:
            Max amount of test URLs to create for any single endpoint
        failed_request_limit:
            Stop testing the API after this many errors
            (useful if multiple tested URLs return the same error message)
        methods_to_test:
            Default: ['GET']
            List of HTTPS methods to test.
            Notice: for HTTP methods that contain a 'requestObject',
            `parameter_values_generator` must be specified if you want to send
            some JSON payload
        parameter_constraints:
            Described in `README.md`
        after_examples_generated:
            Described in `README.md`
        after_error_occurred:
            Function that would be called in case of any errors
        before_request_send:
            A pre-hook that allows to amend the request object

    Returns:
        None

    Raises:
        AssertionError - if API schema is incorrect
        Exception - if generated URL does not meet the API schema requirements
    """
    if methods_to_test is None:
        methods_to_test = ["GET"]

    methods_to_test = [method.lower() for method in methods_to_test]

    base_url = schema.schema.servers[0].url

    failed_requests = 0

    def should_continue_on_fail() -> bool:
        nonlocal failed_requests

        failed_requests += 1
        if failed_requests > failed_request_limit:
            print(
                colored(
                    "Amount of failed requests exceeded the limit (%s)"
                    % failed_request_limit,
                    "red",
                )
            )
            return False
        return True

    for endpoint_name, endpoint_data in schema.schema.paths.items():

        for method in methods_to_test:
            if (
                hasattr(endpoint_data, method)
                and getattr(endpoint_data, method) is not None
            ):
                test_endpoint(
                    endpoint_name=endpoint_name,
                    method=method,
                    base_url=base_url,
                    should_continue_on_fail=should_continue_on_fail,
                    schema=schema,
                    max_urls_per_endpoint=max_urls_per_endpoint,
                    parameter_constraints=parameter_constraints,
                    after_error_occurred=after_error_occurred,
                    after_examples_generated=after_examples_generated,
                    before_request_send=None
                    if before_request_send is None
                    else lambda request_object: before_request_send(
                        endpoint_name,
                        request_object,
                    ),
                )

                if failed_requests > failed_request_limit:
                    return
