"""This module provides REST services for service objects"""
import cherrypy
# import cherrypy_cors

from LmRex.services.api.v1.map import MapLM
from LmRex.services.api.v1.name import (NameGBIF, NameITISSolr, NameTentacles)
from LmRex.services.api.v1.occ import (
    OccGBIF, DatasetGBIF, OccIDB, OccMopho, OccSpecify, OccTentacles)
from LmRex.services.api.v1.resolve import SpecifyResolve

from LmRex.common.lmconstants import (CHERRYPY_CONFIG_FILE)

# .............................................................................
def CORS():
    """This function enables Cross-Origin Resource Sharing (CORS)
    for a web request.

    Function to be called before processing a request.  This will add response
    headers required for CORS (Cross-Origin Resource Sharing) requests.  This
    is needed for browsers running JavaScript code from a different domain.
    """
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers[
        'Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Credentials'] = 'true'
    if cherrypy.request.method.lower() == 'options':
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return 'OK'
    
# .............................................................................
def start_cherrypy_services():
    conf = {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()} 
        }
    # .............................................................................
    # Tell CherryPy to add headers needed for CORS
#     cherrypy_cors.install()
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
#     cherrypy.config.update(CHERRYPY_CONFIG_FILE)
    cherrypy.config.update(
        {'server.socket_port': 80,
         'server.socket_host': '129.237.201.192',
         'log.error_file': '/state/partition1/lmscratch/log/cherrypyErrors.log',
         'log.access_file': '/state/partition1/lmscratch/log/cherrypyAccess.log',
         'response.timeout': 1000000,
         'tools.CORS.on': True,
         'tools.encode.encoding': 'utf-8',
         'tools.encode.on': True,
         'tools.etags.autotags': True,
         'tools.sessions.on': True,
         'tools.sessions.storage_class': cherrypy.lib.sessions.FileSession,
         'tools.sessions.storage_path': '/state/partition1/lmscratch/sessions',
         '/static': {
             'tools.staticdir.on': True,
             'cors.expose.on': True
             }
         })

    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    
    # ARK service
    cherrypy.tree.mount(SpecifyResolve(), SpecifyResolve.endpoint(), conf)

    # Occurrence services
    cherrypy.tree.mount(OccTentacles(), OccTentacles.endpoint(), conf)
    cherrypy.tree.mount(OccGBIF(), OccGBIF.endpoint(), conf)
    cherrypy.tree.mount(OccIDB(), OccIDB.endpoint(), conf)
    cherrypy.tree.mount(OccMopho(), OccMopho.endpoint(), conf)
    cherrypy.tree.mount(OccSpecify(), OccSpecify.endpoint(), conf)
    # Occurrence by dataset
    cherrypy.tree.mount(DatasetGBIF(), DatasetGBIF.endpoint(), conf)
    # Map services
    cherrypy.tree.mount(MapLM(), MapLM.endpoint(), conf)
    # Name services
    cherrypy.tree.mount(NameTentacles(), NameTentacles.endpoint(), conf)
    cherrypy.tree.mount(NameGBIF(), NameGBIF.endpoint(), conf)
    cherrypy.tree.mount(NameITISSolr(), NameITISSolr.endpoint(), conf)   

    cherrypy.engine.start()
    cherrypy.engine.block()

# .............................................................................
if __name__ == '__main__':
    """
    Example calls:
        curl http://129.237.201.192/sparks/2c1becd5-e641-4e83-b3f5-76a55206539a
        curl http://129.237.201.192/api/v1/occ/idb/2c1becd5-e641-4e83-b3f5-76a55206539a
    """
    start_cherrypy_services()
    