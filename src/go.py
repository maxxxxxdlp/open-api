import os
import requests
import subprocess
import xml.etree.ElementTree as ET
import zipfile
import cherrypy
import json

from LmRex.tools.api import APIQuery, GbifAPI, IdigbioAPI
from LmRex.fileop.readwrite import (
    get_csv_dict_reader, get_csv_dict_writer,  get_line)
from LmRex.fileop.ready_file import ready_filename, delete_file
import LmRex.tools.solr as spsolr
from LmRex.common.lmconstants import (
    SPECIFY_ARK_PREFIX, GBIF, DWCA, ENCODING, TEST_SPECIFY7_SERVER, 
    SPECIFY7_RECORD_ENDPOINT, SPECIFY7_SERVER_KEY, SPCOCO_FIELDS, 
    ICH_RSS_URL, KU_IPT_RSS_URL, TEST_GUIDS)

from LmRex.tools.api import SpecifyPortalAPI
from LmRex.api.sparks import SpecifyArk

# .............................................................................
# Test post
# .............................................................................
# fname = '/tmp/kubi_paleobotany/occurrence.solr.csv'
# solr_location = 'notyeti-192.lifemapper.org'
# collection = 'spcoco'
# headers = {'Content-Type': 'text/csv'}
# solr_endpt = 'http://{}:8983/solr'.format(solr_location)
# url = '{}/{}/update'.format(solr_endpt, collection)
# params = {'commit' : 'true'}
# with open(fname, 'r', encoding=ENCODING) as in_file:
#     data = in_file.read()
# response = requests.post(url, data=data, params=params, headers=headers)

# .............................................................................
# Test spocc
# .............................................................................
occid = TEST_GUIDS[0]

if occid is None:
    print('S^n GBIF occurrence resolution is online')
else:
    spark = SpecifyArk()
    arkrec = spark.GET(occid=occid)
    if isinstance(arkrec, dict):
        url = arkrec['url']
        rec = SpecifyPortalAPI.get_specify_record(url)
        print(rec)
    else:
        print('No specify record indexed with GUID {}'.format(occid))
