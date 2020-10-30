import os
import pytest
import shutil
import time

from spcoco.resolve import *
from common.lmconstants import (DWCA)


TEST_SPECIFY_RSS = 'https://ichthyology.specify.ku.edu/export/rss/'
TEST_SPECIFY_URLS = [
    'https://ichthyology.specify.ku.edu/static/depository/export_feed/kui-dwca.zip',
    'https://ichthyology.specify.ku.edu/static/depository/export_feed/kuit-dwca.zip'
]

today = time.localtime()
DATE_STR = '{}.{}.{}'.format(today.tm_year, today.tm_mon, today.tm_mday)

# .............................................................................
class Test_Resolver:
    """Test individual parts of the Specify Resolver."""
    # ............................
    def test_find_links(self):
        urls = get_dwca_urls(TEST_SPECIFY_RSS)
        for url in urls:
            assert(url in TEST_SPECIFY_URLS)
            
    # ............................
    def test_download_link(self):
        test_path, extract_dir, zip_dwca_fname = prep_dwca_data()
        zip_dwca_fullfname = download_dwca(TEST_SPECIFY_URLS[0], test_path)
        assert(os.path.exists(zip_dwca_fullfname))

    # ............................
    def test_extract_dwca(self):
        test_path, extract_dir, zip_dwca_fname = prep_dwca_data(
            do_download=True, do_extract=False)
        zipfname = os.path.join(test_path, zip_dwca_fname)
        extract_path = os.path.join(test_path, extract_dir)
        
        extract_dwca(zipfname, extract_path=extract_path)

        meta_fname = os.path.join(extract_path, DWCA.META_FNAME)
        ds_meta_fname = os.path.join(extract_path, DWCA.DATASET_META_FNAME)
        assert(os.path.exists(meta_fname))
        assert(os.path.exists(ds_meta_fname))
        
        
    # ............................
    def test_read_dwca(self):
        test_path, extract_dir, _ = prep_dwca_data(
            do_download=True, do_extract=True)
        meta_fname = os.path.join(
            test_path, extract_dir, DWCA.META_FNAME)
        ds_meta_fname = os.path.join(
            test_path, extract_dir, DWCA.DATASET_META_FNAME)
        # Read dataset metadata        
        ds_uuid = read_dataset_uuid(ds_meta_fname)
        assert(len(ds_uuid) > 20 and _is_uuid(ds_uuid))
        
        # Read DWCA metadata
        fileinfo = read_core_fileinfo(meta_fname)
        for key in (
            DWCA.DELIMITER_KEY, DWCA.LINE_DELIMITER_KEY, DWCA.QUOTE_CHAR_KEY, 
            DWCA.LOCATION_KEY, DWCA.UUID_KEY, DWCA.FLDMAP_KEY, DWCA.FLDS_KEY):
            # Key exists and is not empty
            assert(key in fileinfo.keys())
            assert(fileinfo[key])

# ...............................................
def _is_uuid(uuidstr):
    if len(uuidstr) <= 30:
        return False
    
    cleanstr = uuidstr.replace('-', '')
    try:
        int(cleanstr, 16)
    except:
        return False
    return True
        
# ...............................................
def _clear_data(path_to_delete):
    """Deletes a file or recursively deletes a directory. """
    if os.path.isdir(path_to_delete):
        try:
            shutil.rmtree(path_to_delete)
        except Exception as e:
            print('Failed to remove directory {}'.format(path_to_delete))
                            
    elif os.path.isfile(path_to_delete):
        try:
            os.remove(path_to_delete)
        except Exception as e:
            print('Failed to remove file {}'.format(path_to_delete))
            
    else:
        print('Path {} does not exist to delete'.format(path_to_delete))
        
# ...............................................
def prep_dwca_data(do_download=False, do_extract=False):
    test_path = '/tmp/test.{}'.format(DATE_STR)
    url = TEST_SPECIFY_URLS[0]
    _, zip_dwca_fname = os.path.split(url)
    extract_dir, _ = os.path.splitext(zip_dwca_fname)
    extract_path = os.path.join(test_path, extract_dir)
    
    # Download DWCA file or clear all test data
    zip_dwca_fullfname = os.path.join(test_path, zip_dwca_fname)
    if do_download:
        if not os.path.exists(zip_dwca_fullfname):
            # download file
            dfname = download_dwca(url, test_path, overwrite=True)
            if os.path.exists(dfname):
                raise Exception('Failed to download {}'.format(url))
    elif os.path.exists(zip_dwca_fullfname):
        _clear_data(test_path)
        
    # Extract DWCA file or clear dwca data
    meta_fname = os.path.join(test_path, extract_dir, DWCA.META_FNAME)
    if do_extract:
        if not os.path.exists(meta_fname):
            extract_dwca(zip_dwca_fullfname, extract_path=extract_path)
    elif os.path.exists(meta_fname):
        _clear_data(extract_path)
    
    return test_path, extract_dir, zip_dwca_fname
    
    # Read record metadata
    """
    fileinfo[DWCA.LOCATION_KEY] = core_loc_elt.text
    fileinfo[DWCA.DELIMITER_KEY] = core_elt.attrib[DWCA.DELIMITER_KEY]
    fileinfo[DWCA.LINE_DELIMITER_KEY] = core_elt.attrib[DWCA.LINE_DELIMITER_KEY]
    fileinfo[DWCA.QUOTE_CHAR_KEY] = core_elt.attrib[DWCA.QUOTE_CHAR_KEY]
    fileinfo['fieldname_index_map'] = field_idxs
    fileinfo['fieldnames'] = ordered_fldnames
    """
    solr_fname = read_recs_for_solr(core_fileinfo, ds_uuid, extract_path)
    print(solr_fname)
