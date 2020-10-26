import cherrypy

from LmRex.spcoco.resolve import (count_docs_in_solr)
from LmRex.tools.solr import (query, query_guid)


collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

class SpecifyArk:
    exposed = True
    
    def __init__(self, content):
        self.content = content
    
    def GET(self, guid=None):    

        if guid is None:
            total = count_docs_in_solr(collection, solr_location)
            return('Specify has {} resolvable guids'.format(total))
        else:
            doc = query_guid(collection, guid, solr_location=solr_location)
            if doc:
                return doc
            else:
                return('No Specify record with the guid {}'.format(guid))

    
if __name__ == '__main__':
    
    cherrypy.tree.mount(
        SpecifyArk(), '/api/spcoco',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
        }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

