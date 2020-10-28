"""This module provides REST services for service objects"""
import cherrypy

from LmRex.api.gocc import GOcc
from LmRex.api.idbocc import IDBOcc
from LmRex.api.sparks import SpecifyArk

# .............................................................................
if __name__ == '__main__':
    """
    Call with 
        curl http://127.0.0.1:8080/api/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()} 
        }

    cherrypy.tree.mount(SpecifyArk(), '/api/sparks', conf)
    cherrypy.tree.mount(GOcc(), '/api/gocc', conf)
    cherrypy.tree.mount(IDBOcc(), '/api/idbocc', conf)

    cherrypy.engine.start()
    cherrypy.engine.block()
