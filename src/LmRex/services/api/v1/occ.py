import cherrypy

from LmRex.common.lmconstants import (S2N, ServiceProvider, APIService)
from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI, BisonAPI)
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.resolve import SpecifyResolve
from LmRex.services.api.v1.dataset import DatasetGBIF
        
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
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
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
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self.get_records(occurrence_id, usr_params['count_only'])


# .............................................................................
@cherrypy.expose
class OccIDB(_OccurrenceSvc):
    PROVIDER = ServiceProvider.iDigBio
    def get_records(self, occid, count_only):
        output = IdigbioAPI.get_occurrences_by_occid(occid, count_only=count_only)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
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
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self.get_records(occurrence_id, usr_params['count_only'])
          
# .............................................................................
@cherrypy.expose
class OccMopho(_OccurrenceSvc):
    PROVIDER = ServiceProvider.MorphoSource
    # ...............................................
    def get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_occurrences_by_occid_page1(
            occid, count_only=count_only)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self.get_records(occurrence_id, usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class OccSpecify(_OccurrenceSvc):
    PROVIDER = ServiceProvider.Specify
    # ...............................................
    def get_records(self, url, occid, count_only):
        msg = 'Spocc failed: url = {}, occid = {}'.format(url, occid)
        if url is None:
            if occid is None:
                output = {'info': 'S^n service is online'}
            else:
                # Specify ARK Record
                spark = SpecifyResolve()
                solr_output = spark.get_specify_guid_meta(occid)
                # Specify Record from URL in ARK
                (url, msg) = spark.get_url_from_meta(solr_output)
                
        if url is not None:
            output = SpecifyPortalAPI.get_specify_record(occid, url, count_only)
            output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        else:
            output = {
                S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [msg], 
                S2N.OCCURRENCE_ID_KEY: occid, S2N.PROVIDER_KEY: self.PROVIDER, 
                S2N.PROVIDER_QUERY_KEY: [url], 
                S2N.SERVICE_KEY: self.SERVICE_TYPE}
        return output 
    
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
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(occid=occid, url=url)
        if usr_params['url'] is None and usr_params['occid'] is None:
            return self._show_online()
        else:
            return self.get_records(
                usr_params['url'], usr_params['occid'], count_only)

# .............................................................................
@cherrypy.expose
class OccTentacles(_OccurrenceSvc):
    # ...............................................
    def get_records(self, usr_params):
        all_output = {S2N.COUNT_KEY: 0, S2N.RECORDS_KEY: []}
        
        occid = usr_params['occid']
        count_only = usr_params['count_only']
        
        # Specify ARK Record
        spark = SpecifyResolve()
        solr_output = spark.get_specify_guid_meta(occid)
        (url, msg) = spark.get_url_from_meta(solr_output)
        # Do not add GUID service record to occurrence records
        # all_output[ServiceProvider.Specify[S2N.NAME_KEY]] = solr_output
        
        # Specify Record from URL in ARK
        if url is not None:
            spocc = OccSpecify()
            sp_output = spocc.get_records(url, occid, count_only)
        else:
            sp_output = {S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [msg]}
        all_output[S2N.RECORDS_KEY].append(
            {ServiceProvider.Specify[S2N.NAME_KEY]: sp_output})
        
        # GBIF copy/s of Specify Record
        gocc = OccGBIF()
        gbif_output = gocc.get_records(occid, count_only)
        all_output[S2N.RECORDS_KEY].append(
            {ServiceProvider.GBIF[S2N.NAME_KEY]: gbif_output})
        
        # iDigBio copy/s of Specify Record
        idbocc = OccIDB()
        idb_output = idbocc.get_records(occid, count_only)
        all_output[S2N.RECORDS_KEY].append(
            {ServiceProvider.iDigBio[S2N.NAME_KEY]: idb_output})
        
        # MorphoSource records connected to Specify Record
        mopho = OccMopho()
        mopho_output = mopho.get_records(occid, count_only)
        all_output[S2N.RECORDS_KEY].append(
            {ServiceProvider.MorphoSource[S2N.NAME_KEY]: mopho_output})

        all_output[S2N.COUNT_KEY] = len(all_output[S2N.RECORDS_KEY])
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
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self.get_records(usr_params)
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES   
    
    print('*** Return invalid URL')
    for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS[:1]:
        # Queries Specify without ARK URL
        spocc = OccSpecify()
        output = spocc.GET(url=None, occid=occid, count_only=False)
        # print results
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
        # print missing elements
        count = 0
        for key in S2N.required_for_occsvc_keys():
            try:
                output[key]
            except:
                count += 1
                print('Missing `{}` output element'.format(key))
        print('Missing {} elements\n'.format(count))

        # Queries GBIF
        api = OccGBIF()
        output = api.GET(occid=occid, count_only=False)
        # print results
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
        # print missing elements
        count = 0
        for key in S2N.required_for_occsvc_keys():
            try:
                output[key]
            except:
                count += 1
                print('Missing `{}` output element'.format(key))
        print('Missing {} elements\n'.format(count))
            
    print('*** Return valid URL')
    for occid in TST_VALUES.GUIDS_W_SPECIFY_ACCESS[:1]:
        # Queries Specify without ARK URL
        spocc = OccSpecify()
        output = spocc.GET(url=None, occid=occid, count_only=False)
        # print results
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
 
        # Queries GBIF
        api = OccGBIF()
        output = api.GET(occid=occid, count_only=False)
        # print results
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
        
    print('*** Tentacles Return invalid URL for Specify, ok for rest')
    for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS[:1]:
        # Queries all services
        s2napi = OccTentacles()
        for count_only in [True, False]:
            required_keys = S2N.required_for_occsvc_keys()
            if count_only is True:
                required_keys = S2N.required_for_occsvc_norecs_keys()
 
            all_output = s2napi.GET(occid=occid, count_only=count_only)
             
            for svcdict in all_output['records']:
                for one_output in svcdict.values():
                    for k, v in one_output.items():
                        print('  {}: {}'.format(k, v))
                    for key in required_keys:
                        try:
                            one_output[key]
                        except:
                            print('Missing `{}` output element'.format(key))
                print('')

