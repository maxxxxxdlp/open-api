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
    def test_one(self, svc, ident, options):
        url = 'http://{}{}/{}'.format(TST_SERVER, svc, ident)
        
        url_params = ''
        for k, v in options.items():
            url_params += '{}={}'.format(k, v)
        
        if url_params:
            url = '{}?{}'.format(url, url_params)
        print(url)
        
        output = self._query_by_url(url)
        try:
            print('  count: {}'.format(output['count']))
        except:
            print('  No count in ouput!')
        try:
            recs = output['records']
        except:
            pass
        else:
            for rec in recs:
                print('  {}'.format(rec))

# ......................................................
    def test_url(self, url):
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
    url = 'http://notyeti-192.lifemapper.org/api/v1/map/lm/Phlox%20longifolia%20Nutt.'
    
    guid = TST_VALUES.FISH_OCC_GUIDS[0]
    for flag in (0,1):
        options = {'count_only': flag}
        tst.test_one(APIMount.OccTentaclesSvc, guid, options)
        tst.test_one(APIMount.GOccSvc, guid, options)
        tst.test_one(APIMount.IDBOccSvc, guid, options)
        tst.test_one(APIMount.MophOccSvc, guid, options)
        tst.test_one(APIMount.SPOccSvc, guid, options)
    
    namestr = TST_VALUES.NAMES[0]
    map_options = {'layers': 'bmng,prj,occ'}
    for flag in (0,1):
        options = {'do_parse': flag}
        tst.test_one(APIMount.NameTentaclesSvc, namestr, options)
        tst.test_one(APIMount.GAcNameSvc, namestr, options)
        tst.test_one(APIMount.ITISSolrNameSvc, namestr, options)
        
        tst.test_one(APIMount.LmMapSvc, namestr, map_options)
