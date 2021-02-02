import typing

RecordsList = typing.List[typing.Dict]

class S2nKey:
    COUNT = 'count'
    RECORD_FORMAT = 'record_format'
    RECORDS = 'records'
    ERRORS = 'errors'
    NAME = 'name'
    OCCURRENCE_ID = 'occurrenceid'
    DATASET_ID = 'dataset_key'
    SERVICE = 'service'
    PROVIDER = 'provider'
    PROVIDER_QUERY = 'provider_query'
    
    @classmethod
    def all_keys(cls):
        return  [
            cls.COUNT, cls.RECORD_FORMAT, cls.RECORDS, cls.ERRORS, cls.NAME, 
            cls.OCCURRENCE_ID, cls.DATASET_ID, cls.SERVICE, cls.PROVIDER, 
            cls.PROVIDER_QUERY]

    @classmethod
    def required_keys(cls):
        return  [
            cls.COUNT, cls.ERRORS, cls.SERVICE, cls.PROVIDER, cls.PROVIDER_QUERY]

    @classmethod
    def required_for_namesvc_keys(cls):
        keys = cls.required_keys()
        keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
        keys.append(cls.NAME)
        return keys
    
    @classmethod
    def required_for_occsvc_keys(cls):
        keys = cls.required_keys()
        keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
        keys.append(cls.OCCURRENCE_ID)
        return keys
    
    @classmethod
    def required_for_occsvc_norecs_keys(cls):
        keys = cls.required_keys()
        keys.append(cls.OCCURRENCE_ID)
        return keys
    
    @classmethod
    def required_for_datasetsvc_keys(cls):
        keys = cls.required_keys()
        keys.extend([cls.RECORD_FORMAT, cls.RECORDS])
        keys.append(cls.DATASET_ID)
        return keys
    
    @classmethod
    def required_for_datasetsvc_norecs_keys(cls):
        keys = cls.required_keys()
        keys.append(cls.DATASET_ID)
        return keys

# Changed to TypedDict on update to Python 3.8+
# This corresponds to the base_response in OpenAPI specification
class S2nOutput(typing.NamedTuple):
    count: int
    provider: str
    errors: typing.List[str]
    provider_query: typing.List[str]
    service: str
    record_format: str = ''
    records: typing.List[dict] = []
    
class S2nError(str):
    pass


