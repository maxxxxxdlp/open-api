"""This module provides REST services for service objects"""
import cherrypy

from LmRex.api.name import (GAcName, ITISName, ITISSolrName, NameSvc)
from LmRex.api.occ import (GOcc, GColl, IDBOcc, MophOcc, SPOcc, OccurrenceSvc)
from LmRex.api.sparks import SpecifyArk

from LmRex.common.lmconstants import (APIMount, CHERRYPY_CONFIG_FILE)

# .............................................................................
def CORS():
    """This function enables CORS for a web request
    Function to be called before processing a request.  This will add response
    headers required for CORS (Cross-Origin Resource Sharing) requests.  This
    is needed for browsers running JavaScript code from a different domain.
    """
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
    cherrypy.response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    cherrypy.response.headers["Access-Control-Allow-Headers"] = "*"
    cherrypy.response.headers["Access-Control-Allow-Credentials"] = "true"
    if cherrypy.request.method.lower() == 'options':
        cherrypy.response.headers['Content-Type'] = 'text/plain'
    return 'OK'

# .............................................................................
def main():
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()} 
        }
    # .............................................................................
    # Tell CherryPy to add headers needed for CORS
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)

#     cherrypy.config.update(CHERRYPY_CONFIG_FILE)
    cherrypy.config.update({'server.socket_port': 80,
                            'server.socket_host': '129.237.201.192'})
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    
    # ARK service
    cherrypy.tree.mount(SpecifyArk(), APIMount.SpecifyArk, conf)

    # Occurrence services
    cherrypy.tree.mount(OccurrenceSvc(), APIMount.OccurrenceSvc, conf)
    cherrypy.tree.mount(GOcc(), APIMount.GOcc, conf)
    cherrypy.tree.mount(IDBOcc(), APIMount.IDBOcc, conf)
    cherrypy.tree.mount(MophOcc(), APIMount.MophOcc, conf)
    cherrypy.tree.mount(SPOcc(), APIMount.SPOcc, conf)
    # Occurrence by dataset
    cherrypy.tree.mount(GColl(), APIMount.GColl, conf)
    
    # Name services
    cherrypy.tree.mount(NameSvc(), APIMount.NameSvc, conf)
    cherrypy.tree.mount(GAcName(), APIMount.GAcName, conf)
    cherrypy.tree.mount(ITISName(), APIMount.ITISName, conf)
    cherrypy.tree.mount(ITISSolrName(), APIMount.ITISSolrName, conf)    

    cherrypy.engine.start()
    cherrypy.engine.block()

# .............................................................................
if __name__ == '__main__':
    """
    Example calls:
        curl http://129.237.201.192/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
        curl http://129.237.201.192/occ/idbocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    main()
