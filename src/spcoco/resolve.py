import argparse
import os
import requests
import subprocess
import xml.etree.ElementTree as ET
import zipfile

from LmRex.tools.api import APIQuery, GbifAPI, IdigbioAPI
from LmRex.tools.readwrite import (
    get_csv_dict_reader, get_csv_dict_writer,  get_line)
from LmRex.tools.ready_file import ready_filename, delete_file
import LmRex.tools.solr as spsolr
from LmRex.common.lmconstants import (
    SPECIFY_ARK_PREFIX, GBIF, DWCA, ENCODING, TEST_SPECIFY7_SERVER, 
    SPECIFY7_RECORD_ENDPOINT, SPECIFY7_SERVER_KEY, SPCOCO_FIELDS, 
    ICH_RSS_URL, KU_IPT_RSS_URL)


INCR_KEY = 0

"""
Pull dataset/record guids from specify RSS
"""

# 'kui-dwca'
kufish = '8f79c802-a58c-447f-99aa-1d6a0790825a'
# 'kuit-dwca'
kufishtish = '56caf05f-1364-4f24-85f6-0c82520c2792'
rec_uuid = '98fb49e0-591b-469e-99af-117b0bfdd7ee'
rurl = '{}/{}/{}/{}'.format(
    TEST_SPECIFY7_SERVER, SPECIFY7_RECORD_ENDPOINT, kufishtish, rec_uuid)

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
    hn = output.strip().decode(ENCODING)
    parts = hn.split('.')
    if parts[0] == 'notyeti-192':
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

def count_docs_in_solr(collection, solr_location=None):
    count = -1
    output = spsolr.query(collection, solr_location=solr_location)
    try:
        count = output['response']['numFound']
    except Exception as e:
        print('Failed to return count {}'.format(e))
    return count

# ......................................................
def _is_guid(idstr):
    try:
        int(idstr.replace('-', ''), 16)
        return True
    except:
        return False

# ......................................................
def read_recs_for_solr(fileinfo, ds_uuid, outpath, overwrite=True):
    """
    Note: 
        Produces data requiring http post to contain 
        headers={'Content-Type': 'text/csv'}
    """
    count = 0
    out_delimiter = ','
    content_type = 'text/csv'
    core_fname = os.path.join(outpath, fileinfo[DWCA.LOCATION_KEY])
    core_fname_noext, _ = os.path.splitext(core_fname)
    solr_outfname = core_fname_noext + '.solr.csv'
    specify_record_server = fileinfo[SPECIFY7_SERVER_KEY]
    
    if os.path.exists(solr_outfname) and overwrite is True:
        _, _ = delete_file(solr_outfname)
    if not os.path.exists(solr_outfname):
        in_delimiter = fileinfo[DWCA.DELIMITER_KEY]
        rdr, inf = get_csv_dict_reader(
            core_fname, in_delimiter, ENCODING, fieldnames=fileinfo['fieldnames'], 
            quote_char=fileinfo[DWCA.QUOTE_CHAR_KEY])
        # Tabs ok?
        wtr, outf = get_csv_dict_writer(
            solr_outfname, out_delimiter, ENCODING, SPCOCO_FIELDS, fmode='w')
        try:
            wtr.writeheader()
            for dwc_rec in rdr:
                solr_rec = {}
                try:
                    count += 1
                    occ_uuid = dwc_rec[fileinfo[DWCA.UUID_KEY]]
                    if not _is_guid(occ_uuid):
                        if count > 1:
                            print('Line {} does not contain a GUID in id field'
                                  .format(count))
                    else:
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
                                solr_rec[fld] =  '{}{}'.format(SPECIFY_ARK_PREFIX, occ_uuid)
                            elif fld == 'url':
                                solr_rec[fld] = '{}/{}/{}'.format(
                                    specify_record_server, ds_uuid, occ_uuid)                        
                        wtr.writerow(solr_rec)
                except Exception as e:
                    print('Rec {}: failed {}'.format(count, e))
        except Exception as e:
            print ('Failed to read/write file {}: {}'.format(core_fname, e))
        finally:
            inf.close()
            outf.close()

    return solr_outfname, content_type, count
        
# ......................................................
def extract_dwca(zip_fname, extract_path=None):
    zfile = zipfile.ZipFile(zip_fname, mode='r', allowZip64=True)
    # unzip zip file stream
    for zinfo in zfile.infolist():
        _, ext = os.path.splitext(zinfo.filename)
        # Check file extension and only unzip valid files
        if ext in ['.xml', '.csv', '.txt']:
            zfile.extract(zinfo, path=extract_path)
        else:
            print('Unexpected filename {} in zipfile {}'.format(
                zinfo.filename, zip_fname))

# ......................................................
def get_dwca_urls(rss_url, isIPT):
    if isIPT:
        ds_ident_key = 'title'
        link_key = '{http://ipt.gbif.org/}dwca'
    else:
        ds_ident_key = 'id'
        link_key = 'link'
    datasets = {}
    api = APIQuery(rss_url)
    api.query_by_get(output_type='xml')
    # API should return XML as ElementTree element
    root = api.output
    elt = root.find('channel')
    ds_elts = elt.findall('item')
    for delt in ds_elts:
        ds_id_elt = delt.find(ds_ident_key)
        url_elt = delt.find(link_key)
        if url_elt is not None:
            if ds_id_elt is None:
                INCR_KEY += 1
                ds_key_val = str(INCR_KEY)
            else:
                ds_key_val = ds_id_elt.text
            datasets[ds_key_val] = {'url': url_elt.text}
    return datasets
    
# ......................................................
def download_dwca(url, baseoutpath, overwrite=False):
    if url.endswith('.zip'):
        _, fname = os.path.split(url)
        basename, _ = os.path.splitext(fname)
        outpath = os.path.join(baseoutpath, basename)
        outfilename = os.path.join(outpath, fname)
    else:
        # IPT link does not contain filename
        idx = url.find('r=')
        tmp = url[idx+2:]
        parts = tmp.split('&')
        if len(parts) == 1:
            name = tmp
        else:
            name = '.'.join(parts)
        outfilename = os.path.join(baseoutpath, name, '{}.zip'.format(name))
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
    idstr = None
    if os.path.split(meta_fname)[1] != 'eml.xml':
        print ('Expected filename eml.xml at {}'.format(meta_fname))
        return ''
    tree = ET.parse(meta_fname)
    root = tree.getroot()
    elt = root.find('dataset')
    id_elts = elt.findall('alternateIdentifier')
    for ie in id_elts:
        idstr = ie.text
        if _is_guid(idstr):
            break
    return idstr

# ......................................................
def _fix_char(ch):
    if not ch:
        ch = None
    elif ch == '\\t':
        ch = '\t'
    elif ch == '\\n':
        ch = '\n'
    elif ch == '':
        ch = None
    return ch
        
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
        fileinfo[DWCA.DELIMITER_KEY] = _fix_char(
            core_elt.attrib[DWCA.DELIMITER_KEY])
        fileinfo[DWCA.LINE_DELIMITER_KEY] = _fix_char(
            core_elt.attrib[DWCA.LINE_DELIMITER_KEY])
        quote_char = _fix_char(
            core_elt.attrib[DWCA.QUOTE_CHAR_KEY])
        fileinfo[DWCA.QUOTE_CHAR_KEY] = quote_char
        # CSV file fields/indices
        # Dictionary of field --> index, index --> field
        # UUID key and index
        uuid_idx = core_elt.find('{}{}'.format(
            DWCA.NS, DWCA.UUID_KEY)).attrib['index']
        # The uuid_idx index --> fieldname 
        #     plus fieldname --> uuid_idx 
        field_idxs[DWCA.UUID_KEY] = uuid_idx
        field_idxs[uuid_idx] = DWCA.UUID_KEY
        all_idxs = [int(uuid_idx)]
        # Rest of fields and indices        
        field_elts = core_elt.findall('{}field'.format(DWCA.NS))
        startidx = len(DWCA.NS)-1
        # Default UUID fieldname
        uuid_fldname = DWCA.UUID_KEY
        for celt in field_elts:
            tmp = celt.attrib['term']
            # strip namespace url from term
            startidx = tmp.rfind('/') + 1
            term = tmp[startidx:]
            idx = celt.attrib['index']
            # Correct UUID fieldname
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

# ...............................................
def get_specify_server(dwca_url):
    prefix = 'http://'
    tmp = dwca_url.lstrip(prefix)
    stop = tmp.find('/')
    specify_url = prefix + tmp[:stop]
    return specify_url

# ...............................................
def main():
    collection = 'spcoco'
    solr_location = 'notyeti-192.lifemapper.org'
    parser = argparse.ArgumentParser(
        description=('Read a zipped DWCA file and index records into Solr.'))
    parser.add_argument(
        '--dwca_file', type=str, default=None,
        help='Zipped DWCA to process')
    parser.add_argument(
        '--rss', type=str, default=ICH_RSS_URL,
        help='URL for RSS feed with download links')    
    parser.add_argument(
        '--outpath', type=str, default='/tmp',
        help='Optional path for DWCA extraction')
    args = parser.parse_args()
    
    zname = args.dwca_file
    dwca_url = args.rss
    outpath = args.outpath
    occguids = [
        '2c1becd5-e641-4e83-b3f5-76a55206539a', 
        'a413b456-0bff-47da-ab26-f074d9be5219',
        'fa7dd78f-8c91-49f5-b01c-f61b3d30caee',
        'db1af4fe-1ed3-11e3-bfac-90b11c41863e',
        'dbe1622c-1ed3-11e3-bfac-90b11c41863e',
        'dcbdb494-1ed3-11e3-bfac-90b11c41863e',
        'dc92869c-1ed3-11e3-bfac-90b11c41863e',
        '21ac6644-5c55-44fd-b258-67eb66ea231d']
    
    isIPT = (dwca_url.find('http://ipt') == 0)
    if dwca_url is not None and not isIPT:
        # Assumes the base RSS/DWCA url is the Specify server
        specify_url = TEST_SPECIFY7_SERVER
    else:
        specify_url = 'unknown_url'
        
    if zname is not None:
        datasets = {'unknown_guid': {'filename': zname}}
    else:        
        datasets = get_dwca_urls(dwca_url, isIPT)
        for guid, meta in datasets.items():
            try:
                url = meta['url']
            except:
                print('Failed to get URL for IPT dataset {}'.format(guid))
            else:
                zipfname = download_dwca(url, outpath)
                meta['filename'] = zipfname
                datasets[guid] = meta
    fixme = []
    for tmp_guid, meta in datasets.items():
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
        core_fileinfo[SPECIFY7_SERVER_KEY] = specify_url
        dwca_guid = read_dataset_uuid(ds_meta_fname)
        # Save new guid for update of datasets dict 
        # if zname argument is provided, we have dataset without guid from download site
        if dwca_guid != tmp_guid:
            print('DWCA meta.xml guid {} conflicts with reported guid {}'
                  .format(dwca_guid, tmp_guid))
            # new/obsolete guid pair
            fixme.append((dwca_guid, tmp_guid))
                   
#         # Read record metadata, dwca_guid takes precedence
#         solr_fname, content_type, rec_count = read_recs_for_solr(
#             core_fileinfo, dwca_guid, extract_path, overwrite=False)         
#         start_count = count_docs_in_solr(collection, solr_location=solr_location)
# 
#         # Post
#         retcode, output = spsolr.post(
#             collection, solr_fname, solr_location=solr_location, 
#             headers={'Content-Type': content_type})
# 
#         # Report old/new solr index count
#         end_count = count_docs_in_solr(collection, solr_location=solr_location)
#         print('Posted, code {}, {} recs in file {} to {}, {} --> {} docs'.format(
#             retcode, rec_count, solr_fname, collection, start_count, end_count))
     
    for new_obsolete_pair in fixme:
        # Remove invalid key
        meta = datasets.pop(new_obsolete_pair[1])
        # Add value back with updated key
        datasets[new_obsolete_pair[0]] = meta
    for oguid in occguids:
        doc = spsolr.query_guid(collection, oguid, solr_location=solr_location)
        print('{}: {}'.format(oguid, doc))
        grecs = GbifAPI.get_specify_record_by_guid(oguid)
        for r in grecs:
            print('  Returned {} with {} issues from collection {}'.format(
                r['acceptedScientificName'], len(r['issues']), r['collectionCode'], oguid))
        irecs = IdigbioAPI.get_specify_record_by_guid(oguid)
        for r in irecs:
            print('  Returned {} with {} flags from collection {}'.format(
                r['data']['dwc:scientificName'], len(r['indexTerms']['flags']), 
                r['data']['dwc:collectionCode'], oguid))
        print()

        

# .............................................................................
if __name__ == '__main__':
    main()

"""
query collection:
https://collections.biodiversity.ku.edu/KU_Fish_tissue/select?q=guid%3A4b650ec9-6bfc-4fd5-bb82-5fe9f345d62b

query portal:
http://preview.specifycloud.org//export/record/56caf05f-1364-4f24-85f6-0c82520c2792/4b650ec9-6bfc-4fd5-bb82-5fe9f345d62b

occguids = [
        '2c1becd5-e641-4e83-b3f5-76a55206539a', 
        'a413b456-0bff-47da-ab26-f074d9be5219',
        'fa7dd78f-8c91-49f5-b01c-f61b3d30caee',
        'db1af4fe-1ed3-11e3-bfac-90b11c41863e',
        'dbe1622c-1ed3-11e3-bfac-90b11c41863e',
        'dcbdb494-1ed3-11e3-bfac-90b11c41863e',
        'dc92869c-1ed3-11e3-bfac-90b11c41863e',
        '21ac6644-5c55-44fd-b258-67eb66ea231d']
oguid = occguids[0]

"""