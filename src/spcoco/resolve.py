import argparse
import os
import requests
import xml.etree.ElementTree as ET
import zipfile

from tools.api import APIQuery
from tools.readwrite import (
    get_csv_dict_reader, get_csv_dict_writer,  get_line)
from tools.ready_file import ready_filename
from tools.solr import (post, query, update)
from common.lmconstants import (
    ARK_PREFIX, DWC_RECORD_TITLE, DWCA, ENCODING, REC_URL, SPCOCO_FIELDS)
from symbol import term
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
                if fld == 'occurrence_guid':
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
    urls = []
    api = APIQuery(rss_url)
    api.query_by_get(output_type='xml')
    # API should return XML as ElementTree element
    root = api.output
    elt = root.find('channel')
    ds_elts = elt.findall('item')
    for delt in ds_elts:
        url_elt = delt.find('link')
        if url_elt is not None:
            urls.append(url_elt.text)
    return urls
        
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
    
    zipfnames = []
    if zname is not None:
        zipfnames.append(zname)
    else:        
        urls = get_dwca_urls(dwca_url)
        for url in urls:
            outfilename = download_dwca(url, outpath)
            zipfnames.append(outfilename)
       
    for zipfname in zipfnames:
        extract_path, _ = os.path.split(zipfname)
        meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
        ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)
        if not os.path.exists(meta_fname):
            extract_dwca(zipfname, extract_path=extract_path)
        
        # Read DWCA metadata
        core_fileinfo = read_core_fileinfo(meta_fname)
        # Read dataset metadata        
        ds_uuid = read_dataset_uuid(ds_meta_fname)
                 
        # Read record metadata
        solr_fname = read_recs_for_solr(core_fileinfo, ds_uuid, extract_path)
        post(collection, solr_fname)
        print('Posted file {} to collection {}'.format(collection, solr_fname))
        

# .............................................................................
if __name__ == '__main__':
    main()

