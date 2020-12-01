import cherrypy
from cherrypy.test import helper
import requests

# import LmRex.api.root import start_cherrypy_services 
from LmRex.common.lmconstants import (HTTPStatus, APIMount, TST_VALUES)
from LmRex.tools.lm_xml import fromstring, deserialize
from cherrypy.test.test_config import setup_server

TST_SERVER = 'notyeti-192.lifemapper.org'
occid = TST_VALUES.BIRD_OCC_GUIDS[0]

class SimpleCPTest(helper.CPWebCase):
# ......................................................
    def __init__(self):
        self.response = None
        self.status = None
    
# ......................................................
    def _query_by_url(self, url):
        self.response = None
        self.status = None
        try:
            self.response = requests.get(
                url, headers={'Content-Type': 'application/json'})
        except Exception as e:
            print(
                'Failed on URL {}, ({})'.format(url, str(e)))
        else:
            try:
                output_type = self.response.headers['Content-Type']
            except: 
                output_type = None
            
            self.status = self.response.status_code
            
            if self.response.status_code == HTTPStatus.OK:
                if output_type.endswith('json'):
                    try:
                        output = self.response.json()
                    except Exception as e:
                        tmp = self.response.content
                        output = deserialize(fromstring(tmp))
                elif output_type.endswith('xml'):
                    try:
                        output = fromstring(self.response.text)
                    except Exception as e:
                        output = self.response.text
                else:
                    print('Unrecognized output type {}'.format(output_type))
            else:
                print('Failed on URL {}, code = {}, reason = {}'.format(
                    url, self.response.status_code, self.response.reason))
        return output
    
# ......................................................
#     @staticmethod
#     def setup_server():
#         # from LmRex.api.root
#         start_cherrypy_services()

    def test_get_counts(self):
        for namestr in TST_VALUES.NAMES:
            do_parse = True
            url = 'http://{}{}/{}'.format(
                TST_SERVER, APIMount.GNameCountOcc, namestr)
            output = self._query_by_url(url)
            print(namestr, output)
# ......................................................
    def test_get_fish(self):
        for svc in APIMount.occurrence_services():
            url = 'http://{}{}'.format(TST_SERVER, svc)
            output = self._query_by_url(url)
#             self.assertEqual(200, self.status)
            print('Returned status {}, output {} from {}'.format(
                self.status, output, url))
            for guid in TST_VALUES.FISH_OCC_GUIDS:
                url = '{}{}/{}'.format(TST_SERVER, svc, guid)
                output = self._query_by_url(url)
                print(guid, output)
                
# .............................................................................
if __name__ == '__main__':
    tst = SimpleCPTest()
    import socket
    hname = socket.gethostname()
#     if hname == TST_SERVER:
#         tst.setup_server()
#     tst.test_get_fish()
    tst.test_get_counts()
