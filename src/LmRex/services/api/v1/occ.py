import cherrypy

from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI)
from LmRex.services.api.v1.sparks import SpecifyArk
from LmRex.services.api.v1.s2nsvc import S2nService

# .............................................................................
def convert_to_bool(obj):
    try:
        obj = obj.lower()
    except:
        pass
    if obj in (0, '0', 'no', 'false'):
        return False
    else:
        return True
        
# .............................................................................
@cherrypy.expose
class OccurrenceSvc(S2nService):

    # ...............................................
    @cherrypy.tools.json_out()
    def _get_params(self, **kwargs):
#     def GET(self, occid=None, count_only=False, **kwargs):
        """
        Superclass to standardize the parameters for all Occurrence Services
        Get a dictionary with a count, and list of one or more records for a 
        Specify GUID and optional info/error message.
        
        Args:
            kwargs: dictionary of:
                occid: a Specify occurrence GUID, from the occurrenceId field
                count_only: flag indicating whether to return records
        Return:
            a dictionary containing a count and optional list of records 
                corresponding to the Specify GUID and an optional message
        """
        kwarg_defaults = {'occid': (None, ''), 'count_only': False}
        usr_params = self._process_params(kwarg_defaults, kwargs)
        return usr_params

# .............................................................................
@cherrypy.expose
class GOcc(OccurrenceSvc):
    # ...............................................
    def get_gbif_recs(self, occid, count_only):
        output = GbifAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        usr_params = self._get_params(kwargs)
        if usr_params['occid'] is None:
            return {'spcoco.message': 'S^n GBIF occurrence resolution is online'}
        else:
            return self.get_gbif_recs(
                usr_params['occid'], usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class GColl(S2nService):
    # ...............................................
    def get_dataset_recs(self, dataset_key, count_only):
        output = GbifAPI.get_records_by_dataset(dataset_key, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        kwarg_defaults = {'dataset_key': (None, ''), 'count_only': True}
        usr_params = self._process_params(kwarg_defaults, kwargs)
        if usr_params['dataset_key'] is None:
            return {'spcoco.message': 'S^n GBIF dataset query is online'}
        else:
            return self.get_dataset_recs(
                usr_params['dataset_key'], usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class IDBOcc(OccurrenceSvc):
    # ...............................................
    def get_idb_recs(self, occid, count_only):
        output = IdigbioAPI.get_records_by_occid(occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get a one or more iDigBio records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a occurrenceId for a specimen record(s)
        Return:
            a dictionary containing a message, or a list of dictionaries 
            containing iDigBio record corresponding to the occurrenceId
        """
        usr_params = self._get_params(kwargs)
        if usr_params['occid'] is None:
            return {'message': 'S^n iDigBio occurrence resolution is online'}
        else:
            return self.get_idb_recs(
                usr_params['occid'], usr_params['count_only'])


# .............................................................................
@cherrypy.expose
class MophOcc(OccurrenceSvc):
    # ...............................................
    def get_mopho_recs(self, occid, count_only):
        output = MorphoSourceAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get a one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: an occurrenceId string
        Return:
            one dictionary containing a message or a list of MorphoSource 
            records corresponding to the occurrenceId
        """
        usr_params = self._get_params(kwargs)
        if usr_params['occid'] is None:
            return {'spcoco.message': 
                    'S^n MorphoSource occurrence resolution is online'}
        else:
            return self.get_mopho_recs(
                usr_params['occid'], usr_params['count_only'])

# .............................................................................
@cherrypy.expose
class SPOcc(OccurrenceSvc):
    # ...............................................
    def get_specify_rec(self, occid):
        output = {}
        spark = SpecifyArk()
        solr_output = spark.get_specify_arc_rec(occid=occid)
        try:
            recs = solr_output['docs']
        except Exception as e:
            output['error'] = 'Failed to return ARK from Specify Resolver'
        else:
            try:
                url = recs[0]['url']
            except:
                output['error'] = 'Failed to return URL from Specify GUID ARK'
            else:
                output = SpecifyPortalAPI.get_specify_record(url)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        """Get one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
            kwargs: ignore unsupported keyword args (i.e. count_only)
        Return:
            one dictionary containing a message or Specify record corresponding 
            to the Specify GUID
        """
        usr_params = self._get_params(kwargs)
        if usr_params['occid'] is None:
            return {'spcoco.message': 'S^n Specify occurrence resolution is online'}
        else:
            return self.get_specify_rec(usr_params['occid'])

# .............................................................................
@cherrypy.expose
class OccTentaclesSvc(OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyArk()
        solr_output = spark.GET(occid=occid)
        all_output['Specify ARK'] = solr_output
#         try:
#             solr_doc = solr_output['docs'][0]
#         except:
#             solr_doc = {}
#         else:
#             if count_only:
#                 solr_output.pop('docs')
#             all_output['Specify ARK'] = solr_output
#         # Get url from ARK for Specify query
#         try:
#             url = solr_doc['url']
#         except Exception as e:
#             pass
#         else:
#             if not url.startswith('http'):
#                 sp_output = {
#                     'warning': 'Invalid URL {} returned from ARK'.format(url)}
#             else:
#                 # Original Specify Record
#                 spocc = SPOcc()
#                 sp_output = SPOcc.GET(url)
#                 if count_only:
#                     sp_output.pop('records')
#             all_output['Specify Record'] = sp_output

        spocc = SPOcc()
        sp_output = spocc.GET(occid=occid)
        all_output['Specify Record'] = sp_output   
        # GBIF copy/s of Specify Record
        gocc = GOcc()
        gbif_output = gocc.GET(occid=occid, count_only=count_only)
        all_output['GBIF Records'] = gbif_output
        # iDigBio copy/s of Specify Record
        idbocc = IDBOcc()
        idb_output = idbocc.GET(occid=occid, count_only=count_only)
        all_output['iDigBio Records'] = idb_output
        
        mopho = MophOcc()
        mopho_output = mopho.GET(occid=occid, count_only=count_only)
        all_output['MorphoSource Records'] = mopho_output
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        usr_params = self._get_params(kwargs)
        if usr_params['occid'] is None:
            return {'message': 'S^n occurrence tentacles are online'}
        else:
            return self.get_records(occid, count_only)
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    count_only = False
    dsid = TST_VALUES.FISH_DS_GUIDS[0]
    
#     s2napi = GColl()
#     gdoutput = s2napi.GET(dataset_key=dsid, count_only=count_only)
#     print(gdoutput)
#     print('')
    
    for occid in TST_VALUES.BIRD_OCC_GUIDS:
        print(occid)
        # Queries all services
        s2napi = GOcc()
        output = s2napi.GET(occid=occid, count_only=count_only)
#         s2napi = OccurrenceSvc()
#         output = s2napi.GET(occid=occid, count_only=count_only)
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
