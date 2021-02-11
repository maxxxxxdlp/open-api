import argparse
import os
import subprocess

from LmRex.common.lmconstants import (
    ENCODING, TEST_SPECIFY7_SERVER, SPECIFY7_RECORD_ENDPOINT, DWCA,
    SPECIFY7_SERVER_KEY, ICH_RSS_URL, KU_IPT_RSS_URL)
from LmRex.fileop.logtools import (LMLog, log_info, log_warn, log_error)
from LmRex.tools.dwca import (DwCArchive, get_dwca_urls, download_dwca)
import LmRex.tools.solr as SpSolr


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
    return hn

# ......................................................
def is_uuid(uuidstr):
    if len(uuidstr) <= 30:
        return False
    
    cleanstr = uuidstr.replace('-', '')
    try:
        int(cleanstr, 16)
    except:
        return False
    return True

# ...............................................
def get_specify_server(dwca_url):
    prefix = 'http://'
    tmp = dwca_url.lstrip(prefix)
    stop = tmp.find('/')
    specify_url = prefix + tmp[:stop]
    return specify_url

# ...............................................
def get_logger_for_processing(logpath, logname=None):
    import time
    if logname is None:
        nm, _ = os.path.splitext(os.path.basename(__file__))
        logname = '{}.{}'.format(nm, int(time.time()))
    logfname = os.path.join(logpath, '{}.log'.format(logname))
    logger = LMLog(logname, logfname)
    return logger

# ...............................................
def main(zname, dwca_url, outpath, solr_location, testguids=[]):
    logger = get_logger_for_processing(outpath)
    # IPT url does not host Specify occurrence server
    isIPT = (dwca_url.find('http://ipt') == 0)
    if dwca_url is not None and not isIPT:
        # Assumes the base RSS/DWCA url is the Specify server
        specify_url = TEST_SPECIFY7_SERVER
    else:
        specify_url = 'unknown_url'
        
    # Existing Zipfile
    if zname is not None:
        datasets = {'unknown_guid': {'filename': zname}}
    # Download Zipfiles and save info on each
    else:        
        datasets = get_dwca_urls(dwca_url, isIPT=isIPT)
        for guid, meta in datasets.items():
            try:
                url = meta['url']
            except:
                log_warn(
                    'Failed to get URL for IPT dataset {}'.format(guid), 
                    logger=logger)
            else:
                zipfname = download_dwca(url, outpath, overwrite=False)
                meta['filename'] = zipfname
                datasets[guid] = meta
    fixme = []
    # Process Zipfiles
    for tmp_guid, meta in datasets.items():
        try:
            zipfname = meta['filename']
        except:
            log_warn(
                'Failed to download data for IPT dataset {}'.format(guid),
                logger=logger)
        else:
            dwca = DwCArchive(zipfname, logger=logger)
            
            extract_path, _ = os.path.split(zipfname)
            meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
            ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)
            # Extract if needed
            if not os.path.exists(meta_fname):
                dwca.extract_from_zip(zipfname, extract_path=extract_path)
          
        # Read DWCA and dataset metadata
        core_fileinfo = dwca.read_core_fileinfo(meta_fname)
        core_fileinfo[SPECIFY7_SERVER_KEY] = specify_url
        dwca_guid = dwca.read_dataset_uuid(ds_meta_fname)
        # Save new guid for update of datasets dict 
        # if zname argument is provided, we have dataset without guid from download site
        if is_guid(tmp_guid) and dwca_guid != tmp_guid:
            log_info(
                'DWCA meta.xml guid {} conflicts with reported guid {}'.format(
                    dwca_guid, tmp_guid), logger=logger)
            # new/obsolete guid pair
            fixme.append((dwca_guid, tmp_guid))
                   
        # Read record metadata, dwca_guid takes precedence
        solr_fname, content_type, is_new = dwca.rewrite_recs_for_solr(
            core_fileinfo, dwca_guid, extract_path, overwrite=False)         
 
        # Post
        if is_new:
            start_count = SpSolr.count_docs(collection, solr_location=solr_location)
            retcode, output = SpSolr.post(
                collection, solr_fname, solr_location=solr_location, 
                headers={'Content-Type': content_type})
     
            # Report old/new solr index count
            end_count = SpSolr.count_docs(collection, solr_location=solr_location)
            log_info(
                'Posted, code {}, to {}, {} --> {} docs'.format(
                    retcode, collection, start_count, end_count), logger=logger)

    # May use dataset guid somewhere
    for new_obsolete_pair in fixme:
        # Remove invalid key
        meta = datasets.pop(new_obsolete_pair[1])
        # Add value back with updated key
        datasets[new_obsolete_pair[0]] = meta

        

# .............................................................................
if __name__ == '__main__':
    collection = 'spcoco'
    solr_location = 'notyeti-192.lifemapper.org'
    test_rss = KU_IPT_RSS_URL
    test_rss = ICH_RSS_URL
    
    parser = argparse.ArgumentParser(
        description=('Read a zipped DWCA file and index records into Solr.'))
    parser.add_argument(
        '--dwca_file', type=str, default=None,
        help='Zipped DWCA to process')
    parser.add_argument(
        '--rss', type=str, default=test_rss,
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
    
    main(zname, dwca_url, outpath, solr_location, testguids=occguids)

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