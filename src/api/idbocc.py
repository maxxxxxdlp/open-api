import cherrypy

from LmRex.tools.api import IdigbioAPI

# .............................................................................
@cherrypy.expose
class IDBOcc:
    
    # ...............................................
    def get_idb_rec(self, occid):
        recs = IdigbioAPI.get_specify_record_by_guid(occid)
        if len(recs) == 0:
            return {'spcoco.error': 
                    'No iDigBio records with the occurrenceId {}'.format(occid)}
        elif len(recs) == 1:
            return recs[0]
        else:
            return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a one or more iDigBio records for a Specify GUID or 
        info/error message.
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            one dictionary or a list of dictionaries.  Each dictionary contains
            a message or iDigBio record corresponding to the Specify GUID
        """
        if occid is None:
            return {'message': 'S^n iDigBio occurrence resolution is online'}
        else:
            return self.get_idb_rec(occid)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/idbocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        IDBOcc(), '/api/idbocc',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

