import cherrypy

from LmRex.tools.api import SpecifyPortalAPI
from LmRex.api.v1.occ import OccIDB, OccGBIF
from LmRex.api.v1.resolve import SpecifyResolve

# .............................................................................
@cherrypy.expose
class Testp:
    
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
    def _get_records(self, occid, count_only):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyResolve()
        rec = spark.get_specify_guid_meta(occid=occid)
        all_output['Specify ARK'] = self._assemble_output([rec], count_only)
        # Get url from ARK for Specify query
        try:
            url = rec['url']
        except Exception as e:
            pass
        else:
            # Original Specify Record
            rec = SpecifyPortalAPI.get_specify_record(url)
            all_output['Specify Record'] = self._assemble_output(
                [rec], count_only)
            
        # GBIF copy/s of Specify Record
        gocc = GOcc()
        recs = gocc.get_gbif_rec(occid)
        all_output['GBIF Records'] = self._assemble_output(recs, count_only)
        # iDigBio copy/s of Specify Record
        idbocc = IDBOcc()
        recs = idbocc.get_idb_rec(occid)
        all_output['iDigBio Records'] = self._assemble_output(recs, count_only)
        return all_output


    # ...............................................
    @cherrypy.tools.json_out()
    def pull_records(self, occid=None):
        if occid is None:
            return {'message': 'S^n occurrence tentacles are online'}
        else:
            return self._get_records(occid, True)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/testp/get_records?occid=2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        Testp(), '/api/testp',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

