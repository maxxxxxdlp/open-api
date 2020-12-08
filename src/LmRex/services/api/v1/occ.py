import cherrypy

from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI)
from LmRex.services.api.v1.sparks import SpecifyArk

def convert_to_bool(obj):
    try:
        obj = obj.lower()
    except:
        pass
    if obj in (1, 'yes', 'true'):
        return True
    else:
        return False
    
# .............................................................................
@cherrypy.expose
class GOcc:
    # ...............................................
    def get_gbif_recs(self, occid, count_only):
        output = GbifAPI.get_specimen_records_by_occid(
            occid, count_only=count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=False, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            a dictionary containing a message or a count and optional list of 
            GBIF records corresponding to the Specify GUID
        """
        count_only = convert_to_bool(count_only)
        if occid is None:
            return {'spcoco.message': 'S^n GBIF occurrence resolution is online'}
        else:
            return self.get_gbif_recs(occid, count_only)

# .............................................................................
@cherrypy.expose
class GColl:
    # ...............................................
    def get_dataset_recs(self, dataset_key, count_only):
        output = GbifAPI.get_records_by_dataset(dataset_key, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=True, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        if dataset_key is None:
            return {'spcoco.message': 'S^n GBIF dataset query is online'}
        else:
            print('Dataset_key {}, count_only {}, kwargs {}'.format(
                dataset_key, count_only, kwargs))
            return self.get_dataset_recs(dataset_key, count_only)

# .............................................................................
@cherrypy.expose
class IDBOcc:
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
        count_only = convert_to_bool(count_only)
        if occid is None:
            return {'message': 'S^n iDigBio occurrence resolution is online'}
        else:
            print('occid {}, count_only {}, kwargs {}'.format(
                occid, count_only, kwargs))
            return self.get_idb_recs(occid, count_only)


# .............................................................................
@cherrypy.expose
class MophOcc:
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
        count_only = convert_to_bool(count_only)
        if occid is None:
            return {'spcoco.message': 
                    'S^n MorphoSource occurrence resolution is online'}
        else:
            print('occid {}, count_only {}, kwargs {}'.format(
                occid, count_only, kwargs))
            return self.get_mopho_recs(occid, count_only)

# .............................................................................
@cherrypy.expose
class SPOcc:
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
    def GET(self, occid=None, **kwargs):
        """Get one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
            kwargs: ignore unsupported keyword args (i.e. count_only)
        Return:
            one dictionary containing a message or Specify record corresponding 
            to the Specify GUID
        """
        if occid is None:
            return {'spcoco.message': 'S^n Specify occurrence resolution is online'}
        else:
            print('occid {}, kwargs {}'.format(
                occid, kwargs))
            return self.get_specify_rec(occid)

# .............................................................................
@cherrypy.expose
class OccurrenceSvc:
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
    def GET(self, occid=None, count_only=False, **kwargs):
        count_only = convert_to_bool(count_only)
        if occid is None:
            return {'message': 'S^n occurrence tentacles are online'}
        else:
            print('occid {}, count_only {}, kwargs {}'.format(
                occid, count_only, kwargs))
            return self.get_records(occid, count_only)
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    count_only = True
    dsid = TST_VALUES.FISH_DS_GUIDS[0]
    
    s2napi = GColl()
    gdoutput = s2napi.GET(dataset_key=dsid, count_only=count_only)
    print(gdoutput)
    print('')
    
    for occid in TST_VALUES.BIRD_OCC_GUIDS:
        print(occid)
        # Queries all services
        s2napi = OccurrenceSvc()
        output = s2napi.GET(occid=occid, count_only=count_only)
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
        print('')
