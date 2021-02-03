import typing

RecordsList = typing.List[typing.Dict]

class S2nKey:
    # standard service output keys
    COUNT = 'count'
    RECORD_FORMAT = 'record_format'
    RECORDS = 'records'
    ERRORS = 'errors'
    QUERY_TERM = 'query_term'
    SERVICE = 'service'
    PROVIDER = 'provider'
    PROVIDER_QUERY = 'provider_query'
    # other S2N constant keys
    NAME = 'name'
    OCCURRENCE_COUNT = 'occurrence_count'
    OCCURRENCE_URL = 'occurrence_url'
    
    @classmethod
    def all_keys(cls):
        return  [
            cls.COUNT, cls.RECORD_FORMAT, cls.RECORDS, cls.ERRORS,  
            cls.QUERY_TERM, cls.SERVICE, cls.PROVIDER, cls.PROVIDER_QUERY]

    @classmethod
    def required_keys(cls):
        return  [
            cls.COUNT, cls.ERRORS, cls.QUERY_TERM, cls.SERVICE, cls.PROVIDER, 
            cls.PROVIDER_QUERY]

    @classmethod
    def required_with_recs_keys(cls):
        return  [
            cls.COUNT, cls.RECORD_FORMAT, cls.RECORDS, cls.ERRORS, 
            cls.QUERY_TERM, cls.SERVICE, cls.PROVIDER, cls.PROVIDER_QUERY]
#     @classmethod
#     def required_for_namesvc_keys(cls):
#         keys = cls.required_keys()
#         keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
#         keys.append(cls.NAME)
#         return keys
#     
#     @classmethod
#     def required_for_occsvc_keys(cls):
#         keys = cls.required_keys()
#         keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
#         keys.append(cls.OCCURRENCE_ID)
#         return keys
#     
#     @classmethod
#     def required_for_occsvc_norecs_keys(cls):
#         keys = cls.required_keys()
#         keys.append(cls.OCCURRENCE_ID)
#         return keys
#     
#     @classmethod
#     def required_for_datasetsvc_keys(cls):
#         keys = cls.required_keys()
#         keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
#         keys.append(cls.DATASET_ID)
#         return keys
#     
#     @classmethod
#     def required_for_datasetsvc_norecs_keys(cls):
#         keys = cls.required_keys()
#         keys.append(cls.DATASET_ID)
#         return keys

# Changed to TypedDict on update to Python 3.8+
# This corresponds to the base_response in OpenAPI specification
class S2nOutput(typing.NamedTuple):
    count: int
    provider: str
    errors: typing.List[str]
    provider_query: typing.List[str]
    query_term: str
    service: str
    record_format: str = ''
    records: typing.List[dict] = []
    
class S2nError(str):
    pass


def print_s2n_output(out_obj):
    try:
        print('count: {}'.format(out_obj.count))
    except:
        print('Missing count element')
    try:
        print('provider: {}'.format(out_obj.provider))
    except:
        print('Missing provider element')
    try:
        print('errors: {}'.format(out_obj.errors))
    except:
        print('Missing errors element')
    try:
        print('provider_query: {}'.format(out_obj.provider_query))
    except:
        print('Missing provider_query element')
    try:
        print('query_term: {}'.format(out_obj.query_term))
    except:
        print('Missing query_term element')
    try:
        print('service: {}'.format(out_obj.service))
    except:
        print('Missing service element')
    try:
        print('record_format: {}'.format(out_obj.record_format))
    except:
        print('Missing record_format element')
    try:
        print('records: {}'.format(out_obj.records))
    except:
        print('Missing records element')


