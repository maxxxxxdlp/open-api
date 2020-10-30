import cherrypy
import json

from LmRex.tools.api import SpecifyPortalAPI
from LmRex.api.gocc import GOcc
from LmRex.api.idbocc import IDBOcc
from LmRex.api.spocc import SPOcc
from LmRex.api.sparks import SpecifyArk

# .............................................................................
@cherrypy.expose
class Tentacles:
    
    # ...............................................
    def assemble_output(self, records, count_only):
        if count_only:
            svc_output = 0
        else:
            svc_output = []
        # records should be a list of dictionaries, fix if single
        if isinstance(records, dict):
            records = [records]
        for rec in records:
            # Informational records use 'spcoco.' prefix for keys
            for k in rec.keys():
                if k.startswith('spcoco'):
                    break
            if count_only:
                svc_output += 1
            else:
                svc_output.append(rec)
        return svc_output
    
    # ...............................................
    def get_records(self, occid, count_only=False):
        all_output = {}
        # Specify ARK Record
        spark = SpecifyArk()
        rec = spark.get_specify_arc_rec(occid=occid)
        all_output['Specify ARK'] = self.assemble_output(
            [rec], count_only=count_only)
        # Get url from ARK for Specify query
        try:
            url = rec['url']
        except Exception as e:
            pass
        else:
            # Original Specify Record
            rec = SpecifyPortalAPI.get_specify_record(url)
            all_output['Specify Record'] = self.assemble_output(
                [rec], count_only=count_only)
            
        # GBIF copy/s of Specify Record
        gocc = GOcc()
        recs = gocc.get_gbif_rec(occid)
        all_output['GBIF Records'] = self.assemble_output(
            recs, count_only=count_only)
        # iDigBio copy/s of Specify Record
        idbocc = IDBOcc()
        recs = idbocc.get_gbif_rec(occid)
        all_output['iDigBio Records'] = self.assemble_output(
            recs, count_only=count_only)

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        if occid is None:
            return {'message': 'S^n occurrence tentacles are online'}
        else:
            return self.get_records(occid)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/gocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        Tentacles(), '/api/tentacles',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

