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
        output = None
        response = None
        status = None
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.get(url, headers=headers)
        except Exception as e:
            print('Failed on URL {}, ({})'.format(url, e))
        else:
            try:
                output_type = response.headers['Content-Type']
            except: 
                output_type = None
            
            status = response.status_code
            
            if status == HTTPStatus.OK:
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
#     def test_get_counts(self):
#         for namestr in TST_VALUES.NAMES:
#             do_parse = True
#             url = 'http://{}{}/{}'.format(
#                 TST_SERVER, APIMount.GAcNameSvc, namestr)
#             output = self._query_by_url(url)
#             print(namestr, output)

# ......................................................
    def test_get_fish(self):
        for svc in APIMount.occurrence_services():
            url = 'http://{}{}'.format(TST_SERVER, svc)
            output = self._query_by_url(url)
            print('Returned status {}, output {} from {}'.format(
                self.status, output, url))
            for guid in TST_VALUES.FISH_OCC_GUIDS:
                url = 'http://{}{}/{}'.format(TST_SERVER, svc, guid)
                output = self._query_by_url(url)
                print(guid, output)
                
# ......................................................
    def test_one(self, svc, ident):
        baseurl = 'http://{}{}'.format(TST_SERVER, svc)
        for x in ident:
            print(x)
            for count_flag in (0, 1):
                url = '{}/{}?count_only={}'.format(baseurl, x, count_flag)
                print(url)
                output = self._query_by_url(url)
                for k, v in output.items():
                    print('  {}: {}'.format(k, v))

# .............................................................................
if __name__ == '__main__':
    tst = SimpleCPTest()
    import socket
    hname = socket.gethostname()

#     tst.test_get_fish()

    guids = TST_VALUES.FISH_OCC_GUIDS[:1]
    tst.test_one(APIMount.GOccSvc, guids)
    tst.test_one(APIMount.IDBOccSvc, guids)
    tst.test_one(APIMount.MophOccSvc, guids)
    tst.test_one(APIMount.SPOccSvc, guids)
