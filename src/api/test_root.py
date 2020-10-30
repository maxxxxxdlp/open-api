import cherrypy
from cherrypy.test import helper

from LmRex.api.gocc import GOcc
from LmRex.api.idbocc import IDBOcc
from LmRex.api.sparks import SpecifyArk

from LmRex.common.lmconstants import TEST_GUIDS

class SimpleCPTest(helper.CPWebCase):
    occid = TEST_GUIDS[0]
    
# ......................................................
    @staticmethod
    def setup_server():
        conf = {
            '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()} 
            }
        
        cherrypy.tree.mount(SpecifyArk(), '/api/sparks', conf)
        cherrypy.tree.mount(GOcc(), '/api/gocc', conf)
        cherrypy.tree.mount(IDBOcc(), '/api/idbocc', conf)
    
        cherrypy.engine.start()
        cherrypy.engine.block()

# ......................................................
    def test_sparks(self):
        self.getPage("/api/sparks")
        self.assertStatus('200 OK')
        self.getPage('/api/sparks/{}'.format(self.occid))
        self.assertStatus('200 OK')

# ......................................................
    def test_get(self):
        self.getPage('/api/sparks/{}'.format(self.occid))
        self.assertStatus('200 OK')

