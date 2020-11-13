"""This module provides REST services for service objects"""
import cherrypy

from LmRex.api.name import (GAcName, ITISName, ITISSolrName, NameSvc)
from LmRex.api.occ import (GOcc, GColl, IDBOcc, SPOcc, OccurrenceSvc)
from LmRex.api.sparks import SpecifyArk

from LmRex.common.lmconstants import (CHERRYPY_CONFIG_FILE)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://129.237.201.192/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
        curl http://129.237.201.192/tentacles/occ/idbocc/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()} 
        }
    
#     cherrypy.config.update(CHERRYPY_CONFIG_FILE)
    cherrypy.config.update({'server.socket_port': 80,
                            'server.socket_host': '129.237.201.192'})
    
    # ARK service
    cherrypy.tree.mount(SpecifyArk(), '/tentacles/sparks', conf)

    # GBIF, iDigBio, Specifyoccurrence services
    cherrypy.tree.mount(GOcc(), '/tentacles/occ/gbif', conf)
    cherrypy.tree.mount(IDBOcc(), '/tentacles/occ/idb', conf)
    cherrypy.tree.mount(SPOcc(), '/tentacles/occ/specify', conf)
    cherrypy.tree.mount(GColl(), '/tentacles/occ/gbif/dataset', conf)
    # combined
    cherrypy.tree.mount(OccurrenceSvc(), '/tentacles/occ', conf)
    
    # GBIF, ITIS name(s) services
    cherrypy.tree.mount(GAcName(), '/tentacles/name/gbif', conf)
    cherrypy.tree.mount(ITISName(), '/tentacles/name/itis', conf)
    cherrypy.tree.mount(ITISSolrName(), '/tentacles/name/itis2', conf)
    # combined
    cherrypy.tree.mount(NameSvc(), '/tentacles/name', conf)
    

    cherrypy.engine.start()
    cherrypy.engine.block()
