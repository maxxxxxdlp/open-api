from LmRex.common.lmconstants import (
    DWC, JSON_HEADERS, ServiceProvider, TST_VALUES)
from LmRex.services.api.v1.s2n_type import S2nKey, S2nOutput
from LmRex.tools.provider.api import APIQuery

# .............................................................................
class SpecifyPortalAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
    PROVIDER = ServiceProvider.Specify['name']
    # ...............................................
    def __init__(self, url=None, logger=None):
        """Constructor for SpecifyPortalAPI class"""
        if url is None:
            url = 'http://preview.specifycloud.org/export/record'
        APIQuery.__init__(self, url, headers=JSON_HEADERS, logger=logger)


    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_only=False, err=None):
        stdrecs = []
        total = 0
        errmsgs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        try:
            recs = [output]
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            total = len(recs)
        # Records
        if not count_only:
            for r in recs:
                try:
                    stdrecs.append(cls._standardize_record(r))
                except Exception as e:
                    msg = cls._get_error_message(err=e)
                    errmsgs.append(msg)

        # TODO: make sure Specify is using full DWC                    
        std_output = S2nOutput(
            count=total, record_format=DWC.SCHEMA, records=stdrecs, 
            provider=cls.PROVIDER, errors=errmsgs, 
            provider_query=None, query_term=None, service=None)

        return std_output

    # ...............................................
    @classmethod
    def get_specify_record(cls, occid, url, count_only, logger=None):
        """Return Specify record published at this url.  
        
        Args:
            url: direct url endpoint for source Specify occurrence record
            
        Note:
            Specify records/datasets without a server endpoint may be cataloged
            in the Solr Specify Resolver but are not resolvable to the host 
            database.  URLs returned for these records begin with 'unknown_url'.
        """
        std_output = {S2nKey.COUNT: 0}
        qry_meta = {
            S2nKey.QUERY_TERM: occid, S2nKey.PROVIDER: cls.PROVIDER,
            S2nKey.PROVIDER_QUERY: [url]}
        
        if url.startswith('http'):
            api = APIQuery(url, headers=JSON_HEADERS, logger=logger)
    
            try:
                api.query_by_get()
            except Exception as e:
                std_output = {
                    S2nKey.COUNT: 0, 
                    S2nKey.ERRORS: [cls._get_error_message(err=e)]}
            else:
                std_output = cls._standardize_output(api.output, count_only)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
        return std_output




