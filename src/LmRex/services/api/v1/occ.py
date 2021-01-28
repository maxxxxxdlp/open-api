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
    # ...............................................
    def get_records(self, occid, count_only):
        output = GbifAPI.get_occurrences_by_occid(
            occid, count_only=count_only)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
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
    def get_records(self, occid, count_only):
        output = IdigbioAPI.get_occurrences_by_occid(occid, count_only=count_only)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
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
    # ...............................................
    def get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_occurrences_by_occid_page1(
            occid, count_only=count_only)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self.get_records(occurrence_id, usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class OccSpecify(_OccurrenceSvc):
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
            output = SpecifyPortalAPI.get_specify_record(url, count_only)
        else:
            output = {S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [msg]}
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
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
        all_output = {'count': 0, 'records': []}
        all_count = 0
        
        occid = usr_params['occid']
        count_only = usr_params['count_only']
        
        # Specify ARK Record
        spark = SpecifyResolve()
        solr_output = spark.get_specify_guid_meta(occid)
        (url, msg) = spark.get_url_from_meta(solr_output)
        # Do not add GUID service record to occurrence records
        # all_output[ServiceProvider.Specify['name']] = solr_output
        
        # Specify Record from URL in ARK
        if url is not None:
            spocc = OccSpecify()
            sp_output = spocc.get_records(url, occid, count_only)
            try:
                all_count += sp_output['count']
            except:
                pass
        else:
            sp_output = {S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [msg]}
        all_output['records'].append(
            {ServiceProvider.Specify['name']: sp_output})
        
        # GBIF copy/s of Specify Record
        gocc = OccGBIF()
        gbif_output = gocc.get_records(occid, count_only)
        try:
            all_count += gbif_output['count']
        except:
            pass
        all_output['records'].append(
            {ServiceProvider.GBIF['name']: gbif_output})
        
        # iDigBio copy/s of Specify Record
        idbocc = OccIDB()
        idb_output = idbocc.get_records(occid, count_only)
        try:
            all_count += idb_output['count']
        except:
            pass
        all_output['records'].append(
            {ServiceProvider.iDigBio['name']: idb_output})
        
        # MorphoSource records connected to Specify Record
        mopho = OccMopho()
        mopho_output = mopho.get_records(occid, count_only)
        try:
            all_count += mopho_output['count']
        except:
            pass
        all_output['records'].append(
            {ServiceProvider.MorphoSource['name']: mopho_output})
        all_output['count'] = len(all_output['records'])
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
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
        sp_output = spocc.GET(url=None, occid=occid, count_only=False)
        for k, v in sp_output.items():
            print('  {}: {}'.format(k, v))
        print('')

    print('*** Return valid URL')
    for occid in TST_VALUES.GUIDS_W_SPECIFY_ACCESS[:1]:
        # Queries Specify without ARK URL
        spocc = OccSpecify()
        sp_output = spocc.GET(url=None, occid=occid, count_only=False)
        for k, v in sp_output.items():
            print('  {}: {}'.format(k, v))
        print('')

    print('*** Return invalid URL for Specify, ok for rest')
    for occid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS[:1]:
        # Queries all services
        s2napi = OccTentacles()
        for count_only in [True, False]:
            required_keys = S2N.required_for_occsvc_keys()
            if count_only is True:
                required_keys = S2N.required_for_occsvc_norecs_keys()

            all_output = s2napi.GET(occid=occid, count_only=count_only)
            
            for svcdict in all_output['records']:
                for svc, one_output in svcdict.items():
                    for k, v in one_output.items():
                        print('  {}: {}'.format(k, v))
                    
                    for key in required_keys:
                        try:
                            one_output[key]
                        except:
                            print('Missing `{}` output element'.format(key))
    
                print('')

