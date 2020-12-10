import cherrypy

from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI)
from LmRex.services.api.v1.sparks import SpecifyArk
from LmRex.services.api.v1.base import S2nService
        
# .............................................................................
@cherrypy.expose
class OccurrenceSvc(S2nService):

    # ...............................................
    @cherrypy.tools.json_out()
    def _get_params(self, occid=None, count_only=None, url=None):
#     def GET(self, occid=None, count_only=False, **kwargs):
        """
        Superclass to standardize the parameters for all Occurrence Services
        Get a dictionary with a count, and list of one or more records for a 
        Specify GUID and optional info/error message.
        
        Args:
            kwargs: dictionary of:
                occid: a Specify occurrence GUID, from the occurrenceId field
                count_only: flag indicating whether to return records
                url: direct URL to Specify occurrence, only used with SPOcc
        Return:
            a dictionary containing a count and optional list of records 
                corresponding to the Specify GUID and an optional message
        """
        kwarg_defaults = {
            'occid': (None, ''), 'count_only': False, 'url': (None, '')}
        user_kwargs = {'occid': occid, 'count_only': count_only, 'url': url}
        usr_params = self._process_params(kwarg_defaults, user_kwargs)
        return usr_params

    # ...............................................
    @cherrypy.tools.json_out()
    def _get_records_from_params(self, usr_params):
        occid = usr_params['occid']
        count_only = usr_params['count_only']
        if occid is not None:
            return self.get_records(occid, count_only)
        else:
            return {'info': 'S^n service is online'}

# .............................................................................
@cherrypy.expose
class GOcc(OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = GbifAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None):
        usr_params = self._get_params(occid=occid, count_only=count_only)
        return self._get_records_from_params(usr_params)
#     def GET(self, **kwargs):
#         usr_params = self._get_params(**kwargs)
#         return self._get_records_from_params(usr_params)
        
#         usr_params = self._get_params(kwargs)
#         occid = usr_params['occid']
#         count_only = usr_params['count_only']
#         if occid is not None:
#             return self.get_records(occid, count_only)
#         else:
#             return {'info': 'S^n GBIF occurrence resolution is online'}


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
        dataset_key = usr_params['dataset_key']
        count_only = usr_params['count_only']
        if dataset_key is None:
            return {'spcoco.message': 'S^n GBIF dataset query is online'}
        else:
            return self.get_dataset_recs(dataset_key, count_only)

# .............................................................................
@cherrypy.expose
class IDBOcc(OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = IdigbioAPI.get_records_by_occid(occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        """Get a one or more iDigBio records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a occurrenceId for a specimen record(s)
        Return:
            a dictionary containing a message, or a list of dictionaries 
            containing iDigBio record corresponding to the occurrenceId
        """
        usr_params = self._get_params(**kwargs)
        return super().GET(usr_params)


# .............................................................................
@cherrypy.expose
class MophOcc(OccurrenceSvc):
    # ...............................................
    def get_records(self, occid, count_only):
        output = MorphoSourceAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        """Get a one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: an occurrenceId string
        Return:
            one dictionary containing a message or a list of MorphoSource 
            records corresponding to the occurrenceId
        """
        usr_params = self._get_params(**kwargs)
        return super().GET(usr_params)

# .............................................................................
@cherrypy.expose
class SPOcc(OccurrenceSvc):
    # ...............................................
    def get_records(self, url, occid):
        output = {}
        if url is None:
            url = None
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
        if url is not None:
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
        usr_params = self._get_params(**kwargs)
        return super().GET(usr_params)

# .............................................................................
@cherrypy.expose
class OccTentaclesSvc(OccurrenceSvc):
    
    def _get_url_from_spark(self, solr_output):
        url = None
        try:
            solr_doc = solr_output['docs'][0]
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
                        'Invalid URL {} returned from ARK for Specify record access'
                        .format(url))
                    url = None
        return (url, msg)
    
    # ...............................................
    def get_records(self, occid, count_only):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyArk()
        solr_output = spark.get_specify_arc_rec(occid)
        all_output['Specify ARK'] = solr_output
        
        # Specify Record from URL in ARK
        (url, msg) = self._get_url_from_spark(solr_output)
        if url is not None:
            spocc = SPOcc()
            sp_output = spocc.get_records(url, occid)
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
    @cherrypy.tools.json_out()
    def GET(self, **kwargs):
        usr_params = self._get_params(**kwargs)
        return super().GET(usr_params)
        
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
        # Queries GBIF
        s2napi = GOcc()
        print('count_only=1')
        output = s2napi.GET(occid=occid, count_only=1)
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('count_only=0')
        output = s2napi.GET(occid=occid, count_only=0)
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
#         # Queries all services
#         s2napi = OccTentaclesSvc()
#         all_output = s2napi.GET(occid=occid, count_only=count_only)
#         for svc, one_output in all_output.items():
#             print('  {}: {}'.format(svc, one_output))
#             for k, v in one_output.items():
#                 print('  {}: {}'.format(k, v))
#         print('')
