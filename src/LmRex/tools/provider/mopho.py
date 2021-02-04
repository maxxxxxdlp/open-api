from LmRex.common.lmconstants import (
    APIService, MorphoSource, ServiceProvider, TST_VALUES)
from LmRex.fileop.logtools import (log_error, log_info)
from LmRex.services.api.v1.s2n_type import S2nKey, S2nOutput
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

        try:
            api.query_by_get()
        except Exception as e:
            out = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_output(
                api.output, MorphoSource.TOTAL_KEY, MorphoSource.RECORDS_KEY, 
                MorphoSource.RECORD_FORMAT, count_only=count_only, 
                err=api.error)
        
        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[api.url], query_term=occid, 
            service=APIService.Occurrence)
        return full_out

# .............................................................................
if __name__ == '__main__':
    # test
    
    log_info('Mopho records:')
    for guid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS:
        moutput = MorphoSourceAPI.get_occurrences_by_occid_page1(guid)
        for r in moutput[S2nKey.RECORDS]:
            occid = notes = None
            try:
                occid = r['specimen.occurrence_id']
                notes = r['specimen.notes']
            except Exception as e:
                msg = 'Morpho source record exception {}'.format(e)
            else:
                msg = '{}: {}'.format(occid, notes)
            log_info(msg)
