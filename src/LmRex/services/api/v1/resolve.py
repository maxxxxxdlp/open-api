import cherrypy

from LmRex.common.lmconstants import (ServiceProvider, APIService, S2N, SPECIFY)
import LmRex.tools.solr as SpSolr
from LmRex.services.api.v1.base import _S2nService

collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

# .............................................................................
@cherrypy.expose
class _ResolveSvc(_S2nService):
    SERVICE_TYPE = APIService.Resolve

# .............................................................................
@cherrypy.expose
class SpecifyResolve(_ResolveSvc):
    """Query the Specify Resolver with a UUID for a resolvable GUID and URL"""
    PROVIDER = ServiceProvider.Specify
    # ...............................................
    @staticmethod
    def get_url_from_meta(solr_output):
        url = msg = None
        try:
            solr_doc = solr_output[S2N.RECORDS_KEY][0]
        except:
            pass
        else:
            # Get url from ARK for Specify query
            try:
                url = solr_doc['url']
            except Exception as e:
                pass
            else:
                if not url.startswith('http'):
                    msg = (
                        'No direct record access to {} returned from collection {}'
                        .format(url, SPECIFY.RESOLVER_COLLECTION))
                    url = None
        return (url, msg)
    
    # ...............................................
    def get_specify_guid_meta(self, occid):
        output = SpSolr.query_guid(
            occid, SPECIFY.RESOLVER_COLLECTION, SPECIFY.RESOLVER_LOCATION)
        try:
            output[S2N.COUNT_KEY]
        except:
            output[S2N.ERRORS_KEY] = [
                'Failed to return count from collection {} at {}'.format(
                    SPECIFY.RESOLVER_COLLECTION, SPECIFY.RESOLVER_LOCATION)]
        return output

    # ...............................................
    def count_specify_guid_recs(self):
        return SpSolr.count_docs(
            SPECIFY.RESOLVER_COLLECTION, SPECIFY.RESOLVER_LOCATION)

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, **kwargs):
        """Get zero or one record for a Specify identifier from the resolution
        service du jour (DOI, ARK, etc) or get a count of all records indexed
        by this resolution service.
        
        Args:
            occid: an occurrenceID, a DarwinCore field intended for a globally 
                unique identifier (https://dwc.tdwg.org/list/#dwc_occurrenceID)
            kwargs: any additional keyword arguments are ignored

        Return:
            A dictionary of metadata and a count of records found in GBIF and 
            an optional list of records.
                
        Note: 
            There will never be more than one record returned.
        """
        if occid is None:
            return self.count_specify_guid_recs()
        else:
            return self.get_specify_guid_meta(occid)

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS[:1]:
        print(occid)
        # Specify ARK Record
        spark = SpecifyResolve()
        solr_output = spark.GET(occid)
        print (solr_output)
