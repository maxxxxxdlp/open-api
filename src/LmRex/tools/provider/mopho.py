from LmRex.common.lmconstants import (MorphoSource, ServiceProvider, TST_VALUES)
from LmRex.fileop.logtools import (log_error)
from LmRex.services.api.v1.s2n_type import S2nKey
from LmRex.tools.provider.api import APIQuery

# .............................................................................
class MorphoSourceAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
    PROVIDER = ServiceProvider.MorphoSource['name']
    # ...............................................
    def __init__(
            self, resource=MorphoSource.OCC_RESOURCE, q_filters={}, 
            other_filters={}, logger=None):
        """Constructor for MorphoSourceAPI class"""
        url = '{}/{}/{}'.format(
            MorphoSource.URL, MorphoSource.COMMAND, resource)
        APIQuery.__init__(
            self, url, q_filters=q_filters, 
            other_filters=other_filters, logger=logger)

    # ...............................................
    @classmethod
    def _page_occurrences(cls, start, occid, logger=None):
        output = {'curr_count': 0, S2nKey.COUNT: 0, S2nKey.RECORDS: []}
        api = MorphoSourceAPI(
            resource=MorphoSource.OCC_RESOURCE, 
            q_filters={MorphoSource.OCCURRENCEID_KEY: occid},
            other_filters={'start': start, 'limit': MorphoSource.LIMIT})
        try:
            api.query_by_get()
        except Exception as e:
            msg = 'Failed on {}, ({})'.format(api.url, e)
            output[S2nKey.ERRORS] = msg
            log_error(msg, logger=logger)
        else:
            # First query, report count
            data = api.output
            output['curr_count'] = data['returnedResults']
            output[S2nKey.COUNT] = data['totalResults']
            output[S2nKey.RECORDS] = data['results']
        return output

    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def get_occurrences_by_occid_page1(cls, occid, count_only=False, logger=None):
        start = 0
        api = MorphoSourceAPI(
            resource=MorphoSource.OCC_RESOURCE, 
            q_filters={MorphoSource.OCCURRENCEID_KEY: occid},
            other_filters={'start': start, 'limit': MorphoSource.LIMIT})
        qry_meta = {
            S2nKey.OCCURRENCE_ID: occid, S2nKey.PROVIDER: cls.PROVIDER,
            S2nKey.PROVIDER_QUERY: [api.url]}
        
        try:
            api.query_by_get()
        except Exception as e:
            std_output = {
                S2nKey.COUNT: 0, S2nKey.ERRORS: cls._get_error_message(err=e)}
        else:
            std_output = cls._standardize_output(
                api.output, MorphoSource.TOTAL_KEY, MorphoSource.RECORDS_KEY, 
                MorphoSource.RECORD_FORMAT, count_only, err=api.error)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
            # First query, report count
        return std_output

