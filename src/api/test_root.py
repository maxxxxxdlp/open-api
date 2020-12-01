import cherrypy
from cherrypy.test import helper
import requests

from LmRex.api.root import start_cherrypy_services 
from LmRex.common.lmconstants import (HTTPStatus, APIMount, TST_VALUES)
from LmRex.tools.lm_xml import fromstring, deserialize
from cherrypy.test.test_config import setup_server

TST_SERVER = 'notyeti-192.lifemapper.org'

class SimpleCPTest(helper.CPWebCase):
    occid = TST_VALUES.BIRD_OCC_GUIDS[0]
    
# ......................................................
    def _query_by_url(self, url):
        output = None
        try:
            response = requests.get(
                url, headers={'Content-Type': 'application/json'})
        except Exception as e:
            print(
                'Failed on URL {}, ({})'.format(url, str(e)))
        else:
            try:
                output_type = response.headers['Content-Type']
            except: 
                output_type = None
                
            if response.status_code == HTTPStatus.OK:
                if output_type.endswith('json'):
                    try:
                        output = response.json()
                    except Exception as e:
                        tmp = response.content
                        output = deserialize(fromstring(tmp))
                elif output_type.endswith('xml'):
                    try:
                        output = fromstring(response.text)
                    except Exception as e:
                        output = response.text
                else:
                    print('Unrecognized output type {}'.format(output_type))
            else:
                print('Failed on URL {}, code = {}, reason = {}'.format(
                    url, response.status_code, response.reason))
        return output
    
# ......................................................
    @staticmethod
    def setup_server():
        # from LmRex.api.root
        start_cherrypy_services()

# ......................................................
    def test_get_fish(self):
        for svc in APIMount.occurrence_services():
            url = 'http://{}{}'.format(TST_SERVER, svc)
            output = self._query_by_url(url)
#             self.getPage(url)
#             self.assertStatus('200 OK')
            for guid in TST_VALUES.FISH_OCC_GUIDS:
                url = '{}{}/{}'.format(TST_SERVER, svc, guid)
                self._query_by_url(url)
          
# .............................................................................
if __name__ == '__main__':
    tst = SimpleCPTest()
    import socket
    hname = socket.gethostname()
    if hname == TST_SERVER:
        tst.setup_server()
    tst.test_get_fish()

