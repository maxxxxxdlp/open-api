# from open_api_tools.test.full_test import full_test
from open_api_tools.test.chain import chain, Request, Validate
from open_api_tools.common.load_schema import load_schema
import json

schema = load_schema(open_api_schema_location='specify7.json')

def after_error_occurred(*error_message):
    print(error_message)

def before_request_send(_endpoint, request_object):
    if request_object.cookies is None:
        request_object.cookies={}
    request_object.cookies['collection']="4"
    request_object.cookies['csrftoken']='VR9JpVckfpu0XyP4Fuvu3pKwJUg3fGwNbuXFa1HRPUKU8iv0ih0z4fbk2dfatlJ6'
    request_object.cookies['sessionid']='8ae2zvdg1n1gevtsur2gr4f2ks9h9xgl'
    return request_object

"""
full_test(
    schema=schema,
    max_urls_per_endpoint=50,
    failed_request_limit=10,
    parameter_constraints={},
    after_error_occurred = after_error_occurred,
    before_request_send=before_request_send
)
"""

def params(arg, arg1, arg2,):
    raise Exception(arg, arg1, arg2)

chain(
    schema=schema,
    definition=[
        Request(
            method='GET',
            endpoint='/context/login/',
        ),
        Validate(validate=lambda _x: True),
        Request(
            method='GET',
            endpoint='/api/workbench/dataset/',
            parameters=params,
        ),
    ],
    before_request_send=before_request_send,
)