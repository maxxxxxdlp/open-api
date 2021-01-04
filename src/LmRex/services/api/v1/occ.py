import cherrypy

from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI, BisonAPI)
from LmRex.services.api.v1.base import S2nService
from LmRex.services.api.v1.sparks import SpecifyArk
        
# .............................................................................
@cherrypy.expose
class _OccurrenceSvc(S2nService):

#     # ...............................................
#     def _standardize_params(
#             self, occid=None, namestr=None, itis_match=True, dataset_key=None, count_only=None, 
#             url=None):
#         """
#         Standardize the parameters for all Occurrence Services into a dictionary 
#         with all keys as standardized parameter names and values as 
#         correctly-typed user values or defaults. 
#         
#         Args:
#             occid: a Specify occurrence GUID, mapped to the 
#                 dwc:occurrenceId field
#             use_itis: flag indicating whether to match using ITIS first, 
#                 used with BISON
#             dataset_key: a GBIF dataset GUID for returning a set of points, 
#                 used with GBIF
#             count_only: flag indicating whether to return records
#             url: direct URL to Specify occurrence, only used with SPOcc
#         Return:
#             a dictionary containing keys and properly formated values for the
#                 user specified parameters.
#         """
#         kwarg_defaults = {
#             'occid': (None, ''), 'dataset_key': (None, ''), 'count_only': False, 
#             'url': (None, '')}
#         user_kwargs = {
#             'occid': occid, 'dataset_key': dataset_key, 
#             'count_only': count_only, 'url': url}
#         usr_params = self._process_params(kwarg_defaults, user_kwargs)
#         return usr_params

    # ...............................................
    @cherrypy.tools.json_out()
    def _show_online(self, msg):
        return {'info': msg}

# .............................................................................
@cherrypy.expose
class GOcc(_OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = GbifAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records_from_params(usr_params)


# .............................................................................
@cherrypy.expose
class GColl(_OccurrenceSvc):
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
class BColl(_OccurrenceSvc):
    # ...............................................
    def get_recs_for_name(self, namestr, count_only):
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
            return self._show_online('S^n Bison occurrences by name is online')
        else:
            return self._get_records(namestr, count_only)
    
# .............................................................................
@cherrypy.expose
class IDBOcc(_OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = IdigbioAPI.get_records_by_occid(occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records_from_params(usr_params)
          
# .............................................................................
@cherrypy.expose
class MophOcc(_OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records_from_params(usr_params)

# .............................................................................
@cherrypy.expose
class SPOcc(_OccurrenceSvc):
    # ...............................................
    def get_records(self, url, occid):
        msg = 'Spocc failed: url = {}, occid = {}'.format(url, occid)
        if url is None:
            if occid is None:
                output = {'info': 'S^n service is online'}
            else:
                # Specify ARK Record
                spark = SpecifyArk()
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
        return self.get_records(usr_params['url'], usr_params['occid'])

# .............................................................................
@cherrypy.expose
class OccTentaclesSvc(_OccurrenceSvc):
    
    # ...............................................
    def get_records(self, occid, count_only):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyArk()
        solr_output = spark.get_specify_arc_rec(occid)
        all_output['Specify ARK'] = solr_output
        
        # Specify Record from URL in ARK
        (url, msg) = spark.get_url_from_spark(solr_output)
        if url is not None:
            spocc = SPOcc()
            sp_output = spocc.GET(url=url, occid=occid)
        else:
            sp_output = {'error': msg}
        all_output['Specify Record'] = sp_output
        
        # GBIF copy/s of Specify Record
        gocc = GOcc()
        gbif_output = gocc.GET(occid=occid, count_only=count_only)
        all_output['GBIF Records'] = gbif_output
        
        # iDigBio copy/s of Specify Record
        idbocc = IDBOcc()
        idb_output = idbocc.GET(occid=occid, count_only=count_only)
        all_output['iDigBio Records'] = idb_output
        
        # MorphoSource records connected to Specify Record
        mopho = MophOcc()
        mopho_output = mopho.GET(occid=occid, count_only=count_only)
        all_output['MorphoSource Records'] = mopho_output
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records_from_params(usr_params)
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    count_only = False
    dsid = TST_VALUES.FISH_DS_GUIDS[0]
    
    s2napi = GColl()
    gdoutput = s2napi.GET(dataset_key=dsid, count_only=True)
    print(gdoutput)
    print('')
    

    for occid in TST_VALUES.BIRD_OCC_GUIDS[:1]:
        print(occid)
#         # Queries GBIF
#         s2napi = GOcc()
#         print('count_only=0')
#         output = s2napi.GET(occid=occid, count_only=0)
#         for k, v in output.items():
#             print('  {}: {}'.format(k, v))
        # Queries Specify without ARK URL
        spocc = SPOcc()
        sp_output = spocc.GET(url=None, occid=occid, count_only=False)
        for k, v in sp_output.items():
            print('  {}: {}'.format(k, v))

        # Queries all services
        s2napi = OccTentaclesSvc()
        all_output = s2napi.GET(occid=occid, count_only=count_only)
        
        for svc, one_output in all_output.items():
            print('  {}'.format(svc))
            for k, v in one_output.items():
                print('  {}: {}'.format(k, v))
            print('')
