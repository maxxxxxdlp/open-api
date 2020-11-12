"""This module provides REST services for service objects"""
import cherrypy

from LmRex.api.gacname import GAcName
from LmRex.api.gocc import GOcc
from LmRex.api.idbocc import IDBOcc
from LmRex.api.itname import ITISName, ITISSolrName
from LmRex.api.spocc import SPOcc
from LmRex.api.sparks import SpecifyArk
from LmRex.api.occ import OccurrenceSvc

from LmRex.common.lmconstants import (CHERRYPY_CONFIG_FILE)

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
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
    cherrypy.tree.mount(GOcc(), '/tentacles/occ/gocc', conf)
    cherrypy.tree.mount(IDBOcc(), '/tentacles/occ/idbocc', conf)
    cherrypy.tree.mount(SPOcc(), '/tentacles/occ/spocc', conf)
    # combined
    cherrypy.tree.mount(OccurrenceSvc(), '/tentacles/occ', conf)
    
    # GBIF, ITIS name(s) services
    cherrypy.tree.mount(GAcName(), '/tentacles/name/gac', conf)
    cherrypy.tree.mount(ITISName(), '/tentacles/name/itis', conf)
    cherrypy.tree.mount(ITISSolrName(), '/tentacles/name/itis2', conf)
    # combined
    cherrypy.tree.mount(SpecifyArk(), '/tentacles/name', conf)
    

    cherrypy.engine.start()
    cherrypy.engine.block()
