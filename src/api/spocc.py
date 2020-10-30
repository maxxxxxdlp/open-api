import cherrypy
import json

from LmRex.tools.api import SpecifyPortalAPI
from LmRex.api.sparks import SpecifyArk

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
        """Get a one Specify record for a Specify GUID or info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            one dictionary containing a message or Specify record corresponding 
            to the Specify GUID
        """
        if occid is None:
            return {'spcoco.message': 'S^n GBIF occurrence resolution is online'}
        else:
            return self.get_specify_rec(occid)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/gocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        SPOcc(), '/api/spocc',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

