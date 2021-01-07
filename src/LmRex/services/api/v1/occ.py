import cherrypy

from LmRex.common.lmconstants import ServiceProvider, APIService
from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI, BisonAPI)
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.sparks import SpecifyResolve
        
# .............................................................................
@cherrypy.expose
class _OccurrenceSvc(_S2nService):
    SERVICE_TYPE = APIService.Occurrence

# .............................................................................
@cherrypy.expose
class OccGBIF(_OccurrenceSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def _get_records(self, occid, count_only):
        output = GbifAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self._get_records(occurrence_id, usr_params['count_only'])


# .............................................................................
@cherrypy.expose
class DatasetGBIF(_OccurrenceSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def get_dataset_recs(self, dataset_key, count_only):
        output = GbifAPI.get_records_by_dataset(dataset_key, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=None, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
            kwargs: additional keyword arguments - to be ignored
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        usr_params = self._standardize_params(
            dataset_key=dataset_key, count_only=count_only)
        dataset_key = usr_params['dataset_key']
        if not dataset_key:
            return {'spcoco.message': 'S^n GBIF dataset query is online'}
        else:
            return self.get_dataset_recs(dataset_key, usr_params['count_only'])


# .............................................................................
@cherrypy.expose
class DatasetBISON(_OccurrenceSvc):
    PROVIDER = ServiceProvider.BISON
    # ...............................................
    def _get_records(self, namestr, count_only):
        output = BisonAPI.get_occurrences_by_name(namestr, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, match_itis=True, count_only=None, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
            kwargs: additional keyword arguments - to be ignored
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        usr_params = self._standardize_params(
            namestr=namestr, match_itis=match_itis, count_only=count_only)
        namestr = usr_params['namestr']
        if namestr is None:
            return self._show_online()
        else:
            return self._get_records(namestr, usr_params['count_only'])
    
# .............................................................................
@cherrypy.expose
class OccIDB(_OccurrenceSvc):
    PROVIDER = ServiceProvider.iDigBio
    # ...............................................
    def _get_records(self, occid, count_only):
        output = IdigbioAPI.get_records_by_occid(occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self._get_records(occurrence_id, usr_params['count_only'])
          
# .............................................................................
@cherrypy.expose
class OccMopho(_OccurrenceSvc):
    PROVIDER = ServiceProvider.MorphoSource
    # ...............................................
    def _get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        occurrence_id = usr_params['occid']
        if occurrence_id is None:
            return self._show_online()
        else:
            return self._get_records(occurrence_id, usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class OccSpecify(_OccurrenceSvc):
    PROVIDER = ServiceProvider.Specify
    # ...............................................
    def _get_records(self, url, occid):
        msg = 'Spocc failed: url = {}, occid = {}'.format(url, occid)
        if url is None:
            if occid is None:
                output = {'info': 'S^n service is online'}
            else:
                # Specify ARK Record
                spark = SpecifyResolve()
                solr_output = spark.get_specify_arc_rec(occid)
                # Specify Record from URL in ARK
                (url, msg) = spark.get_url_from_spark(solr_output)
                
        if url is not None:
            output = SpecifyPortalAPI.get_specify_record(url)
        else:
            output = {'info': msg}
        return output 
    
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, url=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, url=url)
        if usr_params['url'] is None and usr_params['occid'] is None:
            return self._show_online()
        else:
            return self._get_records(usr_params['url'], usr_params['occid'])

# .............................................................................
@cherrypy.expose
class OccTentacles(_OccurrenceSvc):
    
    # ...............................................
    def _get_records(self, occid, count_only):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyResolve()
        solr_output = spark.get_specify_arc_rec(occid)
        all_output['Specify ARK'] = solr_output
        
        # Specify Record from URL in ARK
        (url, msg) = spark.get_url_from_spark(solr_output)
        if url is not None:
            spocc = OccSpecify()
            sp_output = spocc.GET(url=url, occid=occid)
        else:
            sp_output = {'error': msg}
        all_output['Specify Record'] = sp_output
        
        # GBIF copy/s of Specify Record
        gocc = OccGBIF()
        gbif_output = gocc.GET(occid=occid, count_only=count_only)
        all_output['GBIF Records'] = gbif_output
        
        # iDigBio copy/s of Specify Record
        idbocc = OccIDB()
        idb_output = idbocc.GET(occid=occid, count_only=count_only)
        all_output['iDigBio Records'] = idb_output
        
        # MorphoSource records connected to Specify Record
        mopho = OccMopho()
        mopho_output = mopho.GET(occid=occid, count_only=count_only)
        all_output['MorphoSource Records'] = mopho_output
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records(usr_params['occid'], usr_params['count_only'])
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    count_only = False
    dsid = TST_VALUES.FISH_DS_GUIDS[0]
    
    s2napi = DatasetGBIF()
    gdoutput = s2napi.GET(dataset_key=dsid, count_only=True)
    print(gdoutput)
    print('')
    

    for occid in TST_VALUES.BIRD_OCC_GUIDS[:1]:
        print(occid)
        # Queries Specify without ARK URL
        spocc = OccSpecify()
        sp_output = spocc.GET(url=None, occid=occid, count_only=False)
        for k, v in sp_output.items():
            print('  {}: {}'.format(k, v))

        # Queries all services
        s2napi = OccTentacles()
        all_output = s2napi.GET(occid=occid, count_only=count_only)
        
        for svc, one_output in all_output.items():
            print('  {}'.format(svc))
            for k, v in one_output.items():
                print('  {}: {}'.format(k, v))
            print('')

