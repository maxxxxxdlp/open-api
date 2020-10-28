import cherrypy

from LmRex.spcoco.resolve import (count_docs_in_solr)
from LmRex.tools.solr import (query_guid)

collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

# .............................................................................
@cherrypy.expose
class SpecifyArk:

    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        if occid is None:
            total = count_docs_in_solr(collection, solr_location)
            return('Specify has {} resolvable guids'.format(total))
        else:
            rec = query_guid(collection, occid, solr_location=solr_location)
            if rec:
                return rec
            else:
                return('No Specify doc with the occurrenceId {} :-('.format(occid))


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

