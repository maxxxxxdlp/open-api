import cherrypy

from LmRex.tools.solr import (count_docs, query_guid)

collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

# .............................................................................
@cherrypy.expose
class SpecifyArk:
    """Query the Specify ARK resolver for a GUID"""
    
    # ...............................................
    def get_specify_arc_rec(self, occid):
        rec = query_guid(collection, occid, solr_location=solr_location)
        if not rec:
            rec = {
                'spcoco.error': 
                'Failed to find ARK for Specify occurrence GUID {}'.format(occid)
                }
        return rec

    # ...............................................
    def count_specify_arc_recs(self):
        total = count_docs(collection, solr_location)
        rec = {'spcoco.total': total} 
        return rec

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a single Specify ARK record for a GUID or count the total number 
        of records
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            a single dictionary with a
             * count of records in the resolver or a
             * Specify ARK record
        """
        if occid is None:
            return self.count_specify_arc_recs()
        else:
            return self.get_specify_arc_rec(occid)


# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        SpecifyArk(), '/api/sparks',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

