from openapi_core import create_spec
import json
from src.automated_testing import settings
from requests import Request, Session
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.contrib.requests import RequestsOpenAPIRequest
from openapi_core.validation.response.validators import ResponseValidator
from openapi_core.contrib.requests import RequestsOpenAPIRequestFactory, RequestsOpenAPIResponse, \
	RequestsOpenAPIResponseFactory


# load the schema
with open(settings.OPEN_API_JSON_LOCATION) as file:
	spec_dict = json.loads(file.read())

spec = create_spec(spec_dict)


request = Request('GET','http://notyeti-192.lifemapper.org/api/v1/name/gbif/Acer?gbif_count=1')
prepared_request = request.prepare()
openapi_request = RequestsOpenAPIRequest(request)
validator = RequestValidator(spec)
result = validator.validate(openapi_request)

#result.raise_for_errors()
errors = result.errors

print(errors)

if errors:
	exit()

s = Session()
response = s.send(prepared_request)

openapi_response = RequestsOpenAPIResponse(response)
validator = ResponseValidator(spec)
result = validator.validate(
	RequestsOpenAPIRequestFactory.create(request),
	RequestsOpenAPIResponseFactory.create(response)
)


#result.raise_for_errors()
errors = result.errors
print(errors)