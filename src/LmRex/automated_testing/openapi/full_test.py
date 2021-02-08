import itertools
import functools
import json
import urllib
import random
from termcolor import colored
from typing import Dict, List, Union
from dataclasses import dataclass
from LmRex.frontend.src.parse_schema import api
from LmRex.automated_testing.utils import report_error
from LmRex.automated_testing.openapi.index import make_request
from LmRex.automated_testing.openapi.parameter_constraints import parameter_constraints

base_url = api.servers[0].url

# max amount test URLs to use at any single endpoint
max_urls_per_endpoint = 50
# stop testing the API after this many errors (useful if multiple tested URLs return the same error message)
failed_request_limit = 100


@dataclass
class ParameterData:
    name: str
    location: str
    required: Union[bool, None]
    examples: List[any]
    type: str
    default: Union[bool, None]


def validate_parameter_data(endpoint_name: str, parameter_data: ParameterData):
    try:
        if parameter_data.type != 'boolean' and not parameter_data.examples:
            if not parameter_data.required:
                return 'continue'
            raise AssertionError('Non-bool required parameters must have examples defined')

        if parameter_data.type == 'boolean' and parameter_data.default is None:
            raise AssertionError('Bool parameter must have a default value')

        if parameter_data.default is not None and parameter_data.required:
            raise AssertionError('Parameter can be required or have a default value, but not both')

        if parameter_data.default is None and parameter_data.required is None:
            raise AssertionError('Non-required parameters must have default value assigned')

        if not parameter_data.required and parameter_data.location == 'path':
            raise AssertionError('Parameters that are part of the path must be required')

        if parameter_data.location not in ['path', 'query']:
            raise AssertionError('Only parameters in path or query are supported for validation!')
    except AssertionError as e:
        raise AssertionError('%s (%s -> %s)' % (str(e), endpoint_name, parameter_data.name))


def create_request_url(endpoint_name: str, parameters: List[ParameterData], variation: List[any]) -> str:
    return functools.reduce(
        lambda request_url, index: (
            request_url.replace('{%s}' % parameters[index].name, urllib.parse.quote(str(variation[index])))
            if parameters[index].location == 'path' else
            (
                '%s%s=%s&' % (request_url, parameters[index].name, urllib.parse.quote(str(variation[index])))
                if variation[index] != '' else request_url
            )
        ),
        range(len(variation)),
        '%s%s?' % (base_url, endpoint_name)
    )


def test():
    failed_requests = 0

    for endpoint_name, endpoint_data in api.paths.items():

        print(colored('Begins testing `%s` endpoint' % endpoint_name, 'red'))

        # fetching parameter data and validating it
        parameters: List[ParameterData] = []
        for parameter in endpoint_data.get.parameters:
            parameter_data = ParameterData(
                parameter.name,
                parameter.in_,
                parameter.required,
                [value['value'] for value in parameter.examples.values()] if parameter.examples else [],
                parameter.schema.type,
                parameter.schema.default,
            )

            if validate_parameter_data(endpoint_name, parameter_data) == 'continue':
                continue

            if parameter_data.type == 'boolean':
                parameter_data.examples = [True, False]

            if not parameter_data.required and '' not in parameter_data.examples:
                parameter_data.examples.append('')

            parameters.append(parameter_data)
        parameter_names = list(map(lambda p: p.name, parameters))

        # creating url variations based on parameters
        parameter_variations = list(itertools.product(*map(lambda p: p.examples, parameters)))
        urls = list(map(
            lambda variation: create_request_url(endpoint_name, parameters, variation),
            parameter_variations
        ))

        print('Created %d test URLS for the `%s` endpoint' % (len(urls), endpoint_name))

        # if more than `max_urls_per_endpoint` urls, take a random sample
        if len(urls) > max_urls_per_endpoint:
            urls, parameter_variations = zip(
                *random.sample(
                    list(
                        zip(
                            urls,
                            parameter_variations
                        )
                    ),
                    max_urls_per_endpoint
                )
            )
            print('Downsizing the sample of test URLS to %d' % max_urls_per_endpoint)

        # testing all url variations for validness
        # fetching all the responses
        # validating responses against schema
        responses: Dict[int, object] = { }
        for index, request_url in enumerate(urls):

            print('%s %s' % (
                colored('[%d/%d]' % (index, len(urls)), 'cyan'),
                colored('Fetching response from %s' % request_url, 'blue'))
                  )

            response = make_request(request_url, log_client_error=False)

            if response['type'] != 'success':
                print(colored(json.dumps(response, indent=4, default=str), 'yellow'))
                failed_requests += 1

            if response['type'] == 'invalid_request_url':
                raise Exception(response['type'])

            if failed_requests > failed_request_limit:
                print(colored('Amount of failed requests exceeded the limit (%s)' % failed_request_limit, 'red'))
                exit(1)

            if 'parsed_response' in response:
                responses[index] = response['parsed_response']

        # running tests though constraints
        defined_constraints = {
            parameter_name: constraint_function
            for parameter_name, constraint_function in parameter_constraints.items()
            if parameter_name in parameter_names
        }
        if defined_constraints:
            for request_index, response_data in responses.items():
                for parameter_name, constraint_function in defined_constraints.items():

                    parameter_value = parameter_variations[request_index][parameter_names.index(parameter_name)]
                    if parameter_value == '':
                        parameter_value = parameters[parameter_names.index(parameter_name)].default

                    if not constraint_function(parameter_value, endpoint_name, response_data):
                        error_message = {
                            'type':            'failed_test_constraint',
                            'title':           'Testing constraint failed',
                            'error_status':    'Constraint on the %s, based on a parameter %s failed' % (
                                endpoint_name,
                                parameter_name
                            ),
                            'url':             urls[request_index],
                            'parsed_response': response_data,
                        }
                        report_error(error_message)
                        print(colored(json.dumps(error_message, indent=4, default=str), 'yellow'))


test()
