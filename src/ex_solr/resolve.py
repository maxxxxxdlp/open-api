import argparse
import os
import requests
import xml.etree.ElementTree as ET
import zipfile

from tools.api import APIQuery
from tools.readwrite import (get_csv_dict_reader, get_csv_dict_writer,  get_line)
from tools.solr import post, query, update
from common.lmconstants import (
    ARK_PREFIX, REC_URL, DWCA, ENCODING, SPCOCO_FIELDS)
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
def read_recs_for_solr(core_fname, solr_fname, ds_uuid, corefileinfo):
    
    (ordered_fldnames, guid_idx, field_idxs, fld_delimiter, line_delimiter, 
     quote_char) = corefileinfo
    rdr, inf = get_csv_dict_reader(
        core_fname, fld_delimiter, ENCODING, fieldnames=ordered_fldnames, 
        quote_char=quote_char)
    wtr, outf = get_csv_dict_writer(solr_fname, fld_delimiter, ENCODING, 
                                    SPCOCO_FIELDS, fmode='w')
    try:
        for dwc_rec in rdr:
            solr_rec = {}
            occ_uuid = dwc_rec['id']
            coll_date = '{}-{}-{}'.format(
                dwc_rec['year'], dwc_rec['month'], dwc_rec['day'])
            
            for fld in SPCOCO_FIELDS:
                if fld == 'occ_guid':
                    solr_rec[fld] = occ_uuid
                elif fld == 'organization':
                    solr_rec[fld] = dwc_rec['institutionCode']
                elif fld == 'dataset_guid':
                    solr_rec[fld] = ds_uuid
                elif fld == 'who':
                    solr_rec[fld] = dwc_rec['institutionCode']
                elif fld == 'what':
                    solr_rec[fld] = dwc_rec['basisOfRecord']
                elif fld == 'when':
                    solr_rec[fld] = coll_date
                elif fld == 'where':
                    solr_rec[fld] =  '{}:{}'.format(ARK_PREFIX, occ_uuid)
                elif fld == 'how':
                    solr_rec[fld] = ''
                elif fld == 'redirect_url':
                    solr_rec[fld] = '{}/{}/{}'.format(REC_URL, ds_uuid, occ_uuid)
                elif fld == 'persistence':
                    solr_rec[fld] = 'STABLE'
            wtr.write_record(solr_rec)
    except Exception as e:
        print('Failed to read or write {}'.format(e))
    finally:
        inf.close()
        outf.close()
        
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
        # Check file extension and only unzip valid files
        zfile.extract(zinfo)


# ......................................................
def get_dwca_urls(rss_url):
    urls = []
    api = APIQuery.init_from_url(rss_url)
    api.query_by_get(output_type='xml')
    output = api.output
    
    tree = ET.parse(output)
    root = tree.getroot()
    elt = root.find('channel')
    ds_elts = elt.findall('item')
    for delt in ds_elts:
        url_elt = delt.find('link')
        if url_elt is not None:
            urls.add(url_elt.text)
    return urls
        
# ......................................................
def download_dwca(url, outpath):
#     api = APIQuery.init_from_url(url)
#     api.query_by_get(output_type='xml')
#     output = api.output
    _, fname = os.path.split(url)
    outfilename = os.path.join(outpath, fname)
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
        
    

# ......................................................
def get_dataset_uuid(meta_fname):
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
        except:
            pass
    return uuid
        
# ......................................................
def find_core_fileinfo(meta_fname):
    """fieldsEnclosedBy="&quot;" 
    fieldsTerminatedBy="," 
    linesTerminatedBy="\r\n" 
    rowType="http://rs.tdwg.org/dwc/terms/Occurrence">"""
    if os.path.split(meta_fname)[1] != 'meta.xml':
        print ('Expected filename meta.xml at {}'.format(meta_fname))
        return ''
    field_idxs = {}
    tree = ET.parse(meta_fname)
    root = tree.getroot()
    core_elt = root.find('{}core'.format(DWCA.NS))
    if core_elt.attrib['rowType'] == DWCA.CORE_TYPE:
        fld_delimiter = core_elt.attrib['fieldsTerminatedBy']
        line_delimiter = core_elt.attrib['linesTerminatedBy']
        quote_char = core_elt.attrib['fieldsEnclosedBy']
        core_fname = core_elt.find('{}files'.format(DWCA.NS)).find('{}location').text
        guid_idx = core_elt.find('{}id'.format(DWCA.NS)).attrib['index']
        field_elts = core_elt.findall('field')
        all_idxs = []
        for celt in field_elts:
            term = celt.attrib['term'].lstrip(DWCA.NS)
            idx = celt.attrib['index']
            all_idxs.append(idx)
            field_idxs[idx] = term
            field_idxs[term] = idx
        all_idxs.sort()
        ordered_fldnames = []
        for i in all_idxs:
            ordered_fldnames.append(field_idxs[i])
    core_fileinfo = (ordered_fldnames, guid_idx, field_idxs, fld_delimiter, 
                     line_delimiter, quote_char)
            
    return core_fname, core_fileinfo

# ...............................................
def main():
    test_url = 'https://ichthyology.specify.ku.edu/export/rss/'
    parser = argparse.ArgumentParser(
        description=('Read a zipped DWCA file and index records into Solr.'))
    parser.add_argument(
        '--zipname', type=str, default=None,
        help='Zipped DWCA to process')
    parser.add_argument(
        '--ipt_rss', type=str, default=test_url,
        help='URL for IPT RSS feed with download link')    
    parser.add_argument(
        '--outpath', type=str, default=os.getcwd(), 
        help='Optional path for DWCA extraction')
    args = parser.parse_args()
    
    if args.zipname is None:
        urls = get_dwca_urls(args.ipt_rss)
        for url in urls:
            download_dwca(url, args.outpath)
        
    extract_dwca(args.zipname, extract_path=args.outpath)
    
    meta_fname = os.path.join(args.outpath, DWCA.META_FNAME)
    core_basename, core_fileinfo = find_core_fileinfo(meta_fname)
    core_fname = os.path.join(args.outpath, core_basename)
     
    ds_uuid = get_dataset_uuid(meta_fname)
     
    csv_outfname = read_recs_for_solr(core_fname, ds_uuid, core_fileinfo)
    
    

# .............................................................................
if __name__ == '__main__':
    main()

