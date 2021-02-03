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
    missing = 0
    print('*** S^n output ***')
    elements = {
        'count': out_obj.count, 'provider': out_obj.provider, 
        'errors': out_obj.errors, 'provider_query': out_obj.provider_query, 
        'query_term': out_obj.query_term, 'records': out_obj.records }    
    for name, attelt in elements.items():
        try:
            print('{}: {}'.format(name, attelt))
        except:
            missing += 1
            print('Missing {} element'.format(name))
    print('Missing {} elements'.format(missing))
    print('')


