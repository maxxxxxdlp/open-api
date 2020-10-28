import cherrypy

from LmRex.tools.api import GbifAPI

@cherrypy.expose
class GOcc:

    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        if occid is None:
            return('S^n GBIF occurrence resolution is online')
        else:
            recs = GbifAPI.get_specify_record_by_guid(occid)
            if len(recs) == 0:
                return('No records with the occurrenceId {} :-('.format(occid))
            elif len(recs) == 1:
                return recs[0]
            else:
                return recs


if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/gocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    cherrypy.tree.mount(
        GOcc(), '/api/gocc',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

