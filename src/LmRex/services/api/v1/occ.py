import cherrypy

from LmRex.common.lmconstants import (ServiceProvider, APIService)

from LmRex.tools.provider.bison import BisonAPI
from LmRex.tools.provider.gbif import GbifAPI
from LmRex.tools.provider.idigbio import IdigbioAPI
from LmRex.tools.provider.mopho import MorphoSourceAPI
from LmRex.tools.provider.specify import SpecifyPortalAPI

from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.resolve import SpecifyResolve
from LmRex.services.api.v1.s2n_type import (print_s2n_output, S2nKey, S2nOutput)

# .............................................................................
@cherrypy.expose
class _OccurrenceSvc(_S2nService):
    SERVICE_TYPE = APIService.Occurrence
    
# .............................................................................
@cherrypy.expose
class OccGBIF(_OccurrenceSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def get_records(self, occid, count_only):
        output = GbifAPI.get_occurrences_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dwc:occurrenceID from the 
        GBIF occurrence record service.
        
        Args:
            occid: an occurrenceID, a DarwinCore field intended for a globally 
                unique identifier (https://dwc.tdwg.org/list/#dwc_occurrenceID)
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of GBIF records corresponding to specimen 
            occurrences in the GBIF database
        """
        try:
            usr_params = self._standardize_params(occid=occid, count_only=count_only)
            occurrence_id = usr_params['occid']
            if occurrence_id is None:
                return self._show_online()
            else:
                return self.get_records(occurrence_id, usr_params['count_only'])
        except Exception as e:
            return self.get_failure(query_term=occid, errors=[e])

# .............................................................................
@cherrypy.expose
class OccIDB(_OccurrenceSvc):
    PROVIDER = ServiceProvider.iDigBio
    def get_records(self, occid, count_only):
        output = IdigbioAPI.get_occurrences_by_occid(occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dwc:occurrenceID from the
        iDigBio occurrence record service.
        
        Args:
            occid: an occurrenceID, a DarwinCore field intended for a globally 
                unique identifier (https://dwc.tdwg.org/list/#dwc_occurrenceID)
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of iDigBio records corresponding to specimen 
            occurrences in the iDigBio database
        """
        try:
            usr_params = self._standardize_params(occid=occid, count_only=count_only)
            occurrence_id = usr_params['occid']
            if occurrence_id is None:
                return self._show_online()
            else:
                return self.get_records(occurrence_id, usr_params['count_only'])
        except Exception as e:
            return self.get_failure(query_term=occid, errors=[e])

# .............................................................................
@cherrypy.expose
class OccMopho(_OccurrenceSvc):
    PROVIDER = ServiceProvider.MorphoSource
    # ...............................................
    def get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_occurrences_by_occid_page1(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        try:
            usr_params = self._standardize_params(occid=occid, count_only=count_only)
            occurrence_id = usr_params['occid']
            if occurrence_id is None:
                return self._show_online()
            else:
                return self.get_records(occurrence_id, usr_params['count_only'])
        except Exception as e:
            return self.get_failure(query_term=occid, errors=[e])

# .............................................................................
@cherrypy.expose
class OccSpecify(_OccurrenceSvc):
    PROVIDER = ServiceProvider.Specify
    # ...............................................
    def get_records(self, url, occid, count_only):
        msg = 'Spocc failed: url = {}, occid = {}'.format(url, occid)
        if url is None:
            # Resolve for record URL
            spark = SpecifyResolve()
            solr_output = spark.get_specify_guid_meta(occid)
            (url, msg) = spark.get_url_from_meta(solr_output)
                
        if url is None:
            out = self.get_failure(query_term=occid, errors=[msg])
        else:
            try:
                out = SpecifyPortalAPI.get_specify_record(occid, url, count_only)
            except Exception as e:
                out = self.get_failure(query_term=occid, errors=[e])

        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=self.PROVIDER,
            errors=out.errors, provider_query=out.provider_query,
            query_term=occid, service=self.SERVICE_TYPE)
        return full_out
    
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, url=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dwc:occurrenceID from the
        Specify occurrence record service.
        
        Args:
            occid: an occurrenceID, a DarwinCore field intended for a globally 
                unique identifier (https://dwc.tdwg.org/list/#dwc_occurrenceID)
            url: a URL to directly access the Specify record
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of Specify records corresponding to specimen 
            occurrences in the Specify database
        """
        try:
            usr_params = self._standardize_params(occid=occid, url=url)
            if usr_params['url'] is None and usr_params['occid'] is None:
                return self._show_online()
            else:
                return self.get_records(
                    usr_params['url'], usr_params['occid'], count_only)
        except Exception as e:
            return self.get_failure(query_term=occid, errors=[e])

# .............................................................................
@cherrypy.expose
class OccTentacles(_OccurrenceSvc):
    # ...............................................
    def get_records(self, usr_params):
        all_output = {S2nKey.COUNT: 0, S2nKey.RECORDS: []}
        
        occid = usr_params['occid']
        count_only = usr_params['count_only']
        
        # Specify ARK Record
        spark = SpecifyResolve()
        solr_output = spark.get_specify_guid_meta(occid)
        (url, msg) = spark.get_url_from_meta(solr_output)
        # Do not add GUID service record to occurrence records
        # all_output[ServiceProvider.Specify[S2nKey.NAME]] = solr_output
        
        # Specify Record from URL in ARK
        spocc = OccSpecify()
        sp_output = spocc.get_records(url, occid, count_only)
        all_output[S2nKey.RECORDS].append(
            {ServiceProvider.Specify[S2nKey.NAME]: sp_output})
        
        # GBIF copy/s of Specify Record
        gocc = OccGBIF()
        gbif_output = gocc.get_records(occid, count_only)
        all_output[S2nKey.RECORDS].append(
            {ServiceProvider.GBIF[S2nKey.NAME]: gbif_output})
        
        # iDigBio copy/s of Specify Record
        idbocc = OccIDB()
        idb_output = idbocc.get_records(occid, count_only)
        all_output[S2nKey.RECORDS].append(
            {ServiceProvider.iDigBio[S2nKey.NAME]: idb_output})
        
        # MorphoSource records connected to Specify Record
        mopho = OccMopho()
        mopho_output = mopho.get_records(occid, count_only)
        all_output[S2nKey.RECORDS].append(
            {ServiceProvider.MorphoSource[S2nKey.NAME]: mopho_output})

        all_output[S2nKey.COUNT] = len(all_output[S2nKey.RECORDS])
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dwc:occurrenceID from each
        available occurrence record service.
        
        Args:
            occid: an occurrenceID, a DarwinCore field intended for a globally 
                unique identifier (https://dwc.tdwg.org/list/#dwc_occurrenceID)
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            a dictionary with keys for each service queried.  Values contain 
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of records corresponding to specimen 
            occurrences in the provider database
        """
        try:
            usr_params = self._standardize_params(
                occid=occid, count_only=count_only)
            return self.get_records(usr_params)
        except Exception as e:
            return self.get_failure(query_term=occid, errors=[e])

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES   
    
#     print('*** Return invalid URL')
#     for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS[:1]:
#         # Queries Specify without ARK URL
#         spocc = OccSpecify()
#         output = spocc.GET(url=None, occid=occid, count_only=False)
#         print_s2n_output(output)
#     
    print('*** Return birds from mopho')         
    for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS:
        for cls in [OccMopho]:
            api = cls()
            output = api.GET(occid=occid, count_only=False)
            print_s2n_output(output)

#     print('*** Return valid URL')
#     for occid in TST_VALUES.GUIDS_W_SPECIFY_ACCESS:
#         for cls in [OccGBIF, OccIDB, OccSpecify]:
#             api = cls()
#             output = api.GET(occid=occid, count_only=False)
#             print_s2n_output(output)

#         # Queries all services
#         s2napi = OccTentacles()
#         for count_only in [True, False]:
#             required_keys = S2nKey.required_keys()
#             if count_only is False:
#                 required_keys = S2nKey.required_with_recs_keys()
#   
#             all_output = s2napi.GET(occid=occid, count_only=count_only)
#               
#             for svc in all_output['records']:
#                 for name, s2nout in svc.items():
#                     print(name)
#                     print_s2n_output(s2nout)
#                 print('')

