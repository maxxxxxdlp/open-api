import cherrypy

from LmRex.tools.api import (
    GbifAPI, IdigbioAPI, MorphoSourceAPI, SpecifyPortalAPI)
from LmRex.services.api.v1.sparks import SpecifyArk

# .............................................................................
@cherrypy.expose
class GOcc:
    # ...............................................
    def get_gbif_recs(self, occid):
        recs = GbifAPI.get_specimen_records_by_occid(occid)
        if len(recs) == 0:
            return {'spcoco.error': 
                    'No GBIF records with the occurrenceId {}'.format(occid)}
        else:
            return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            one dictionary or a list of dictionaries.  Each dictionary contains
            a message or GBIF record corresponding to the Specify GUID
        """
        if occid is None:
            return {'spcoco.message': 'S^n GBIF occurrence resolution is online'}
        else:
            return self.get_gbif_recs(occid)

# .............................................................................
@cherrypy.expose
class GColl:
    # ...............................................
    def get_dataset_recs(self, dataset_key):
        recs = GbifAPI.get_records_by_dataset(dataset_key)
        if len(recs) == 0:
            return {'spcoco.error': 
                    'No GBIF records with the dataset_key {}'.format(dataset_key)}
        else:
            return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None):
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
            return self.get_dataset_recs(dataset_key)

# .............................................................................
@cherrypy.expose
class IDBOcc:
    # ...............................................
    def get_idb_recs(self, occid):
        recs = IdigbioAPI.get_records_by_occid(occid)
        if len(recs) == 0:
            return {'spcoco.error': 
                    'No iDigBio records with the occurrenceId {}'.format(occid)}
        else:
            return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a one or more iDigBio records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a occurrenceId for a specimen record(s)
        Return:
            a dictionary containing a message, or a list of dictionaries 
            containing iDigBio record corresponding to the occurrenceId
        """
        if occid is None:
            return {'message': 'S^n iDigBio occurrence resolution is online'}
        else:
            return self.get_idb_recs(occid)


# .............................................................................
@cherrypy.expose
class MophOcc:
    # ...............................................
    def get_mopho_recs(self, occid):
        recs = MorphoSourceAPI.get_specimen_records_by_occid(occid=occid)
        return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: an occurrenceId string
        Return:
            one dictionary containing a message or a list of MorphoSource 
            records corresponding to the occurrenceId
        """
        if occid is None:
            return {'spcoco.message': 
                    'S^n MorphoSource occurrence resolution is online'}
        else:
            return self.get_mopho_recs(occid)

# .............................................................................
@cherrypy.expose
class SPOcc:
    # ...............................................
    def get_specify_rec(self, occid):
        spark = SpecifyArk()
        rec = spark.get_specify_arc_rec(occid=occid)
        try:
            url = rec['url']
        except Exception as e:
            pass
        else:
            rec = SpecifyPortalAPI.get_specify_record(url)
        return rec

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            one dictionary containing a message or Specify record corresponding 
            to the Specify GUID
        """
        if occid is None:
            return {'spcoco.message': 'S^n Specify occurrence resolution is online'}
        else:
            return self.get_specify_rec(occid)

# .............................................................................
@cherrypy.expose
class OccurrenceSvc:
    # ...............................................
    def _assemble_output(self, records, count_only):
        if count_only:
            svc_output = 0
        else:
            svc_output = []
        # Handle dict record/s as a list
        if isinstance(records, dict):
            records = [records]
        for rec in records:
            is_rec = True
            # Error/info records use 'spcoco.' prefix for all keys
            for k in rec.keys():
                if k.startswith('spcoco'):
                    is_rec = False
                    break
            # Do not count error/info records
            if count_only:
                if is_rec:
                    svc_output += 1
            # Return data and error/info records
            else:
                svc_output.append(rec)
        return svc_output
    
    # ...............................................
    def get_records(self, occid, count_only=False):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyArk()
        rec = spark.get_specify_arc_rec(occid=occid)
        all_output['Specify ARK'] = self._assemble_output([rec], count_only)
        # Get url from ARK for Specify query
        try:
            url = rec['url']
        except Exception as e:
            pass
        else:
            if not url.startswith('http'):
                rec = {}
            else:
                # Original Specify Record
                rec = SpecifyPortalAPI.get_specify_record(url)
                all_output['Specify Record'] = self._assemble_output(
                    [rec], count_only)
            
        # GBIF copy/s of Specify Record
        gocc = GOcc()
        recs = gocc.get_gbif_recs(occid)
        all_output['GBIF Records'] = self._assemble_output(recs, count_only)
        # iDigBio copy/s of Specify Record
        idbocc = IDBOcc()
        recs = idbocc.get_idb_recs(occid)
        all_output['iDigBio Records'] = self._assemble_output(recs, count_only)
        
        mopho = MophOcc()
        mopho.get_mopho_recs(occid)
        all_output['MorphoSource Records'] = self._assemble_output(recs, count_only)
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        if occid is None:
            return {'message': 'S^n occurrence tentacles are online'}
        else:
            return self.get_records(occid, count_only=False)
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    gdapi = GColl()
    gdrecs = gdapi.get_dataset_recs(TST_VALUES.FISH_DS_GUIDS[0])

    occid1 = TST_VALUES.FISH_OCC_GUIDS[2]
    occid2 = TST_VALUES.BIRD_OCC_GUIDS[0]
    for occid in [occid2]:
        oapi = OccurrenceSvc()
        orecs = oapi.get_records(occid, count_only=False)
            
        gapi = GOcc()
        grecs = gapi.get_gbif_recs(occid)
    
        iapi = IDBOcc()
        irecs  = iapi.get_idb_recs(occid)
        
        mapi = MophOcc()
        mrecs = mapi.get_mopho_recs(occid)
    
        sapi = SPOcc()
        srecs = sapi.get_specify_rec(occid)
"""

api = OccurrenceSvc()
recs = api.get_records()


"""
