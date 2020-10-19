import argparse
import os
import requests
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from LmRex.tools.api import APIQuery
from LmRex.tools.readwrite import (
    get_csv_dict_reader, get_csv_dict_writer,  get_line)
from LmRex.tools.ready_file import ready_filename
from LmRex.tools.solr import (post, query, query_guid, update)
from LmRex.common.lmconstants import (
    ARK_PREFIX, DWC_RECORD_TITLE, DWCA, ENCODING, REC_URL, SPCOCO_FIELDS)
"""
Pull dataset/record guids from specify RSS
"""

# 'kui-dwca'
kufish = '8f79c802-a58c-447f-99aa-1d6a0790825a'
# 'kuit-dwca'
kufishtish = '56caf05f-1364-4f24-85f6-0c82520c2792'
rec_uuid = '98fb49e0-591b-469e-99af-117b0bfdd7ee'
rurl = '{}/{}/{}'.format(REC_URL, kufishtish, rec_uuid)

# Read RSS feed for download link
# Download and unzip DWCA
# Read eml.xml for dataset UUID
# Read occurrence.csv for specimen UUIDs
# Write fields for solr to CSV
# ......................................................
def _get_server_addr():
    output, _ = subprocess.Popen(
        '/usr/bin/hostname', shell=True, stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE).communicate()
    hn = output.strip()
    parts = hn.split(b'.')
    if parts[0] == b'notyeti-192':
        return 'localhost'
    else:
        return hn

# ......................................................
def _get_date(dwc_rec):
    yr = dwc_rec['year']
    try:
        int(yr)
    except:
        coll_date = ''
    else:
        coll_date = yr 
        
    for val in (dwc_rec['month'], dwc_rec['day']):
        try:
            int(val)
        except:
            return coll_date
        else:
            coll_date = '{}-{}'.format(coll_date, val)
    return coll_date

# ......................................................
def read_recs_for_solr(fileinfo, ds_uuid, outpath):
    core_fname = os.path.join(outpath, fileinfo[DWCA.LOCATION_KEY])
    core_fname_noext, _ = os.path.splitext(core_fname)
    solr_outfname = core_fname_noext + '.solr.csv'
    
    delimiter = fileinfo[DWCA.DELIMITER_KEY]
    rdr, inf = get_csv_dict_reader(
        core_fname, delimiter, ENCODING, fieldnames=fileinfo['fieldnames'], 
        quote_char=fileinfo[DWCA.QUOTE_CHAR_KEY])
    wtr, outf = get_csv_dict_writer(
        solr_outfname, delimiter, ENCODING, SPCOCO_FIELDS, fmode='w')
    try:
        wtr.writeheader()
        for dwc_rec in rdr:
            solr_rec = {}
            occ_uuid = dwc_rec[fileinfo[DWCA.UUID_KEY]]
            coll_date = _get_date(dwc_rec)
            who_val = dwc_rec['datasetName']
            
            for fld in SPCOCO_FIELDS:
                if fld == 'id':
                    solr_rec[fld] = occ_uuid
                elif fld == 'dataset_guid':
                    solr_rec[fld] = ds_uuid
                elif fld == 'who':
                    solr_rec[fld] = who_val
                elif fld == 'what':
                    solr_rec[fld] = dwc_rec['basisOfRecord']
                elif fld == 'when':
                    solr_rec[fld] = coll_date
                elif fld == 'where':
                    solr_rec[fld] =  '{}{}'.format(ARK_PREFIX, occ_uuid)
                elif fld == 'url':
                    solr_rec[fld] = '{}/{}/{}'.format(REC_URL, ds_uuid, occ_uuid)
            wtr.writerow(solr_rec)
    except Exception as e:
        print('Failed to read or write {}'.format(e))
    finally:
        inf.close()
        outf.close()

    return solr_outfname
        
# ......................................................
def extract_dwca(zip_fname, extract_path=None):
    zfile = zipfile.ZipFile(zip_fname, mode='r', allowZip64=True)
    # unzip zip file stream
    for zinfo in zfile.infolist():
        _, ext = os.path.splitext(zinfo.filename)
        # Check file extension and only unzip valid files
        if ext in ['.xml', '.csv']:
            zfile.extract(zinfo, path=extract_path)
        else:
            print('Unexpected filename {} in zipfile {}'.format(
                zinfo.filename, zip_fname))
            break

# ......................................................
def get_dwca_urls(rss_url):
    datasets = {}
    api = APIQuery(rss_url)
    api.query_by_get(output_type='xml')
    # API should return XML as ElementTree element
    root = api.output
    elt = root.find('channel')
    ds_elts = elt.findall('item')
    for delt in ds_elts:
        ds_guid_elt = delt.find('id')
        url_elt = delt.find('link')
        if ds_guid_elt is not None and url_elt is not None:
            datasets[ds_guid_elt.text] = {'url': url_elt.text}
    return datasets
        
# ......................................................
def download_dwca(url, baseoutpath, overwrite=False):
    _, fname = os.path.split(url)
    basename, _ = os.path.splitext(fname)
    outpath = os.path.join(baseoutpath, basename)
    outfilename = os.path.join(outpath, fname)
    success = ready_filename(outfilename, overwrite=overwrite)
    if success:
        ret_code = None
        try:
            response = requests.get(url)
        except Exception as e:
            try:
                ret_code = response.status_code
                reason = response.reason
            except AttributeError:
                reason = 'Unknown Error'
            print(('Failed on URL {}, code = {}, reason = {} ({})'.format(
                url, ret_code, reason, str(e))))
    
        output = response.content
        with open(outfilename, 'wb') as outf:
            outf.write(output)
    return outfilename
    

# ......................................................
def read_dataset_uuid(meta_fname):
    uuid = None
    if os.path.split(meta_fname)[1] != 'eml.xml':
        print ('Expected filename eml.xml at {}'.format(meta_fname))
        return ''
    tree = ET.parse(meta_fname)
    root = tree.getroot()
    elt = root.find('dataset')
    id_elts = elt.findall('alternateIdentifier')
    for ie in id_elts:
        idstr = ie.text
        try:
            int(idstr.replace('-', ''), 16)
            uuid = idstr
            break
        except:
            pass
    return uuid
        
# ......................................................
def read_core_fileinfo(meta_fname):
    """Reads meta.xml file for information about the core occurrence file
    
    Args:
        meta_fname: meta.xml file at the top level of a Darwin Core Archive
        
    Returns:
        Dictionary of core occurrence file information, with keys matching the 
        names/tags in the meta.xml file:
            location (for filename), id (for fieldname of record UUID) 
            fieldsTerminatedBy, linesTerminatedBy, fieldsEnclosedBy, 
        plus: 
            fieldnames: ordered fieldnames 
            fieldname_index_map: dict of fields and corresponding column indices
    """
    if os.path.split(meta_fname)[1] != 'meta.xml':
        print ('Expected filename meta.xml at {}'.format(meta_fname))
        return ''
    fileinfo = {}
    field_idxs = {}
    tree = ET.parse(meta_fname)
    root = tree.getroot()
    core_elt = root.find('{}core'.format(DWCA.NS))
    if core_elt.attrib['rowType'] == DWCA.CORE_TYPE:
        # CSV file name
        core_files_elt = core_elt.find('{}files'.format(DWCA.NS))
        core_loc_elt = core_files_elt.find('{}{}'.format(DWCA.NS, DWCA.LOCATION_KEY))
        fileinfo[DWCA.LOCATION_KEY] = core_loc_elt.text
        # CSV file structure
        fileinfo[DWCA.DELIMITER_KEY] = core_elt.attrib[DWCA.DELIMITER_KEY]
        fileinfo[DWCA.LINE_DELIMITER_KEY] = core_elt.attrib[DWCA.LINE_DELIMITER_KEY]
        fileinfo[DWCA.QUOTE_CHAR_KEY] = core_elt.attrib[DWCA.QUOTE_CHAR_KEY]
        # CSV file fields/indices
        # Dictionary of field --> index, index --> field
        # UUID key and index
        uuid_idx = core_elt.find('{}{}'.format(
            DWCA.NS, DWCA.UUID_KEY)).attrib['index']
        # The uuid_idx index --> fieldname term 
        # Keys will include both 'id' and fieldname term --> uuid_idx
        field_idxs[DWCA.UUID_KEY] = uuid_idx
        # Rest of fields and indices        
        field_elts = core_elt.findall('{}field'.format(DWCA.NS))
        all_idxs = []
        startidx = len(DWCA.NS)-1
        for celt in field_elts:
            tmp = celt.attrib['term']
            # strip namespace url from term
            startidx = tmp.rfind('/') + 1
            term = tmp[startidx:]
            idx = celt.attrib['index']
            if idx == uuid_idx:
                uuid_fldname = term
            all_idxs.append(int(idx))
            field_idxs[idx] = term
            field_idxs[term] = idx
        fileinfo[DWCA.UUID_KEY] = uuid_fldname
        fileinfo[DWCA.FLDMAP_KEY] = field_idxs
        # CSV file fieldnames ordered by column index
        all_idxs.sort()
        ordered_fldnames = []
        for i in all_idxs:
            ordered_fldnames.append(field_idxs[str(i)])
        fileinfo[DWCA.FLDS_KEY] = ordered_fldnames
            
    return fileinfo

# ......................................................
def post_csv_data(collection, fname):
    """Posts csv with fields corresponding to named collection to Solr
    
    Args:
        core_fname: Full path the CSV file containing data to be indexed in Solr
        collection: name of the Solr collection to be posted to 
    """
    post(collection, fname)
    
# ...............................................
def main():
    test_url = 'https://ichthyology.specify.ku.edu/export/rss/'
    collection = 'spcoco'
    parser = argparse.ArgumentParser(
        description=('Read a zipped DWCA file and index records into Solr.'))
    parser.add_argument(
        '--dwca_file', type=str, default=None,
        help='Zipped DWCA to process')
    parser.add_argument(
        '--ipt_rss', type=str, default=test_url,
        help='URL for IPT RSS feed with download link')    
    parser.add_argument(
        '--outpath', type=str, default=os.getcwd(),
        help='Optional path for DWCA extraction')
    args = parser.parse_args()
    
    zname = args.dwca_file
    dwca_url = args.ipt_rss
#     outpath = args.outpath
    outpath = '/tank/data/specify'
    occguids = [
        '2c1becd5-e641-4e83-b3f5-76a55206539a', 
        'a413b456-0bff-47da-ab26-f074d9be5219',
        'fa7dd78f-8c91-49f5-b01c-f61b3d30caee',
        'db1af4fe-1ed3-11e3-bfac-90b11c41863e',
        'dbe1622c-1ed3-11e3-bfac-90b11c41863e',
        'dcbdb494-1ed3-11e3-bfac-90b11c41863e',
        'dc92869c-1ed3-11e3-bfac-90b11c41863e',
        '21ac6644-5c55-44fd-b258-67eb66ea231d']
    addr = _get_server_addr()    
    zipfnames = []
    if zname is not None:
        zipfnames.append(zname)
    else:        
        datasets = get_dwca_urls(dwca_url)
        for guid, meta in datasets.items():
            try:
                url = meta['url']
            except:
                print('Failed to get URL for IPT dataset {}'.format(guid))
            else:
                zipfname = download_dwca(url, outpath)
                meta['filename'] = zipfname
                datasets[guid] = meta
        
    for guid, meta in datasets.items():
        try:
            zipfname = meta['filename']
        except:
            print('Failed to download data for IPT dataset {}'.format(guid))
        else:
            extract_path, _ = os.path.split(zipfname)
            meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
            ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)
            if not os.path.exists(meta_fname):
                extract_dwca(zipfname, extract_path=extract_path)
         
        # Read DWCA and dataset metadata
        core_fileinfo = read_core_fileinfo(meta_fname)
        dwca_guid = read_dataset_uuid(ds_meta_fname)
        if dwca_guid != guid:
            print('DWCA meta.xml guid {} conflicts with RSS reported guid {}')
                  
        # Read record metadata, dwca_guid takes precedence
        solr_fname = read_recs_for_solr(core_fileinfo, dwca_guid, extract_path)
        post(collection, solr_fname, solr_location=addr)
        print('Posted file {} to collection {}'.format(solr_fname, collection))

    for guid in guids:
        res = query_guid(collection, guid)

# .............................................................................
if __name__ == '__main__':
    main()

"""
import os
import requests
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from LmRex.tools.api import APIQuery
from LmRex.tools.readwrite import (
    get_csv_dict_reader, get_csv_dict_writer,  get_line)
from LmRex.tools.ready_file import ready_filename
from LmRex.tools.solr import (post, query, query_guid, update)
from LmRex.common.lmconstants import (
    ARK_PREFIX, DWC_RECORD_TITLE, DWCA, ENCODING, REC_URL, SPCOCO_FIELDS)
from LmRex.spcoco.resolve import *

test_url = 'https://ichthyology.specify.ku.edu/export/rss/'
collection = 'spcoco'
occguids = [
        '2c1becd5-e641-4e83-b3f5-76a55206539a', 
        'a413b456-0bff-47da-ab26-f074d9be5219',
        'fa7dd78f-8c91-49f5-b01c-f61b3d30caee',
        'db1af4fe-1ed3-11e3-bfac-90b11c41863e',
        'dbe1622c-1ed3-11e3-bfac-90b11c41863e',
        'dcbdb494-1ed3-11e3-bfac-90b11c41863e',
        'dc92869c-1ed3-11e3-bfac-90b11c41863e',
        '21ac6644-5c55-44fd-b258-67eb66ea231d']
        
zname = None
dwca_url = test_url

outpath = '/tmp'

addr = _get_server_addr()    

datasets = get_dwca_urls(dwca_url)
for guid, meta in datasets.items():
    try:
        url = meta['url']
    except:
        print('Failed to get URL for IPT dataset {}'.format(guid))
    else:
        zipfname = download_dwca(url, outpath)
        meta['filename'] = zipfname
        datasets[guid] = meta

for guid, meta in datasets.items():
    try:
        zipfname = meta['filename']
    except:
        print('Failed to download data for IPT dataset {}'.format(guid))
    else:
        extract_path, _ = os.path.split(zipfname)
        meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
        ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)
        if not os.path.exists(meta_fname):
            print('Extracting {}'.format(zipfname)
            extract_dwca(zipfname, extract_path=extract_path)
     
     
guid = '8f79c802-a58c-447f-99aa-1d6a0790825a'
meta = datasets[guid]
zipfname = meta['filename']
extract_path, _ = os.path.split(zipfname)
meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)

# Read DWCA and dataset metadata
core_fileinfo = read_core_fileinfo(meta_fname)
dwca_guid = read_dataset_uuid(ds_meta_fname)
if dwca_guid != guid:
    print('DWCA meta.xml guid {} conflicts with RSS reported guid {}')
              
# Read record metadata, dwca_guid takes precedence
solr_fname = read_recs_for_solr(core_fileinfo, dwca_guid, extract_path)

solr_location='localhost'
headers={}
response = output = None
solr_endpt = 'http://{}:8983/solr'.format(solr_location)
url = '{}/{}/update?commit=true'.format(solr_endpt, collection)

post(collection, solr_fname, solr_location=addr)

print('Posted file {} to collection {}'.format(collection, solr_fname))

for oguid in occguids:
    res = query_guid(collection, oguid)

"""