import cherrypy
from cherrypy.test import helper

import LmRex.api.root as LmRoot
from LmRex.common.lmconstants import (TEST_VALUES, APIMount)

    
class SimpleCPTest(helper.CPWebCase):
    occid = TEST_VALUES.BIRD_GUIDS[0]
    
    
# ......................................................
    @staticmethod
    def setup_server():
        # from LmRex.api.root
        LmRoot.main()

# ......................................................
    def test_get(self):
        occ_endpoints = [
            APIMount.SpecifyArk, APIMount.OccurrenceSvc, APIMount.GOcc,
            APIMount.IDBOcc, APIMount.SPOcc, APIMount.GColl]
        ds_endpoints = [APIMount.GColl]
        name_endpoints = [
            APIMount.NameSvc, APIMount.GAcName, APIMount.ITISName, 
            APIMount.ITISSolrName]
        for svc in occ_endpoints:
            self.getPage(svc)
            self.assertStatus('200 OK')
            

