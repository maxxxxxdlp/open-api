import os
import requests
import xml.etree.ElementTree as ET
import zipfile

from LmRex.tools.provider.api import APIQuery
from LmRex.fileop.logtools import (log_info, log_warn, log_error)
from LmRex.fileop.csvtools import (get_csv_dict_reader, get_csv_dict_writer)
from LmRex.fileop.ready_file import ready_filename, delete_file
from LmRex.common.lmconstants import (
    SPECIFY_ARK_PREFIX, DWCA, ENCODING, TEST_SPECIFY7_SERVER, 
    SPECIFY7_RECORD_ENDPOINT, SPECIFY7_SERVER_KEY, SPCOCO_FIELDS)


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
def get_dwca_urls(rss_url, isIPT=False):
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
            datasets[ds_key_val] = {'url': url_elt.text, 'name': ds_key_val}
    return datasets
    
# ......................................................
def assemble_download_filename(url, baseoutpath):
    """Construct the full filename to download a DWCA into, based on the 
    filename to be downloaded or the IPT endpoint containing the DWCA.
    
    Note: Must download DWCA files into different directories, as the contents
    unzip into the top level directory, and identically named files will be 
    overwritten.
    
    """
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
    return outfilename
        
# ......................................................
def download_dwca(url, baseoutpath, overwrite=False, logger=None):
    outfilename = assemble_download_filename(url, baseoutpath)
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
            log_error('Failed on URL {}, code = {}, reason = {} ({})'.format(
                url, ret_code, reason, str(e)), logger)
    
        output = response.content
        with open(outfilename, 'wb') as outf:
            outf.write(output)
    return outfilename

# .............................................................................
class DwCArchive:
    """Class to download and read a Darwin Core Archive"""

    # ......................................................
    def __init__(self, zipfile_or_directory, outpath=None, logger=None):
        """
        Args:
            zipfile_or_directory: Full path to zipfile or directory containing 
                Darwin Core Archive
            outpath: file location for output data and log files
            logger: LMLog object for logging processing information
            
        Note: 
            Produces data requiring http post to contain 
            headers={'Content-Type': 'text/csv'}
        """
        if os.path.exists(zipfile_or_directory):
            self.logger = logger
            # DWCA is zipped
            if (os.path.isfile(zipfile_or_directory) and 
                zipfile_or_directory.endswith('.zip')):
                self.zipfile = zipfile_or_directory
                if outpath is not None:
                    self.dwca_path = outpath
                else:
                    self.dwca_path, _ = os.path.split(zipfile_or_directory)
            # DWCA is ready
            elif os.path.isdir(zipfile_or_directory):
                self.dwca_path = zipfile_or_directory
            # Metadata files
            self.meta_fname = os.path.join(self.dwca_path, DWCA.META_FNAME)
            self.ds_meta_fname = os.path.join(self.dwca_path, DWCA.DATASET_META_FNAME)
        else:
            raise Exception('File or directory {} does not exist'.format(
                zipfile_or_directory))

    # ......................................................
    def _is_guid(self, idstr):
        try:
            int(idstr.replace('-', ''), 16)
            return True
        except:
            return False
    
    # ......................................................
    def _get_date(self, dwc_rec):
        coll_date = ''        
        try:
            yr = dwc_rec['year']
            int(yr)
        except:
            pass
        else:
            coll_date = yr             
            try:
                mo = dwc_rec['month']
                int(mo)
            except:
                pass
            else:
                coll_date = '{}-{}'.format(coll_date, mo)
                try:
                    dy = dwc_rec['day']
                    int(dy)
                except:
                    pass
                else:
                    coll_date = '{}-{}'.format(coll_date, dy)
        return coll_date
    

    # ......................................................
    def rewrite_recs_for_solr(self, fileinfo, ds_uuid, overwrite=True):
        """
        Note: 
            Produces data requiring http post to contain 
            headers={'Content-Type': 'text/csv'}
        """
        count = 0
        is_new = False
        out_delimiter = ','
        content_type = 'text/csv'
        core_fname = os.path.join(self.dwca_path, fileinfo[DWCA.LOCATION_KEY])
        core_fname_noext, _ = os.path.splitext(core_fname)
        solr_outfname = core_fname_noext + '.solr.csv'
        specify_record_server = '{}/{}'.format(
            fileinfo[SPECIFY7_SERVER_KEY], SPECIFY7_RECORD_ENDPOINT)
        
        if os.path.exists(solr_outfname) and overwrite is True:
            _, _ = delete_file(solr_outfname)
        if not os.path.exists(solr_outfname):
            in_delimiter = fileinfo[DWCA.DELIMITER_KEY]
            rdr, inf = get_csv_dict_reader(
                core_fname, in_delimiter, ENCODING, 
                fieldnames=fileinfo['fieldnames'])
            # Tabs ok?
            wtr, outf = get_csv_dict_writer(
                solr_outfname, out_delimiter, ENCODING, SPCOCO_FIELDS, fmode='w')
            try:
                wtr.writeheader()
                bad_guid_count = 0
                for dwc_rec in rdr:
                    solr_rec = {}
                    try:
                        count += 1
                        occ_uuid = dwc_rec[fileinfo[DWCA.UUID_KEY]]
                        if count == 1 and occ_uuid == DWCA.UUID_KEY:
                            pass
                        else:
                            if not self._is_guid(occ_uuid):
                                bad_guid_count += 1
                                if bad_guid_count < 10:
                                    log_warn(
                                        'Line {} contains {}, non-GUID in id field'
                                        .format(count, occ_uuid), 
                                        logger=self.logger)
                                elif bad_guid_count == 10:
                                    log_warn('...', logger=self.logger)
                                
                            coll_date = self._get_date(dwc_rec)
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
                        log_error('Rec {}: failed {}'.format(count, e))
            except Exception as e:
                log_warn(
                    'Failed to read/write file {}: {}'.format(core_fname, e), 
                    logger=self.logger)
            finally:
                inf.close()
                outf.close()
                is_new = True
                log_info(
                    'Wrote {} recs, with {} non-guid-ids to file {}'.format(
                        count, bad_guid_count, solr_outfname), logger=self.logger)
        return solr_outfname, content_type, is_new
        
    # ......................................................
    def extract_from_zip(self, extract_path=None):
        zfile = zipfile.ZipFile(self.zipfile, mode='r', allowZip64=True)
        if extract_path is None:
            extract_path, _ = os.path.split(self.zipfile)
        # unzip zip file stream
        for zinfo in zfile.infolist():
            _, ext = os.path.splitext(zinfo.filename)
            # Check file extension and only unzip valid files
            if ext in ['.xml', '.csv', '.txt']:
                zfile.extract(zinfo, path=extract_path)
            else:
                log_warn('Unexpected filename {} in zipfile {}'.format(
                    zinfo.filename, self.zipfile), logger=self.logger)

    
    # ......................................................
    def read_dataset_uuid(self):
        idstr = None
        if os.path.split(self.ds_meta_fname)[1] != DWCA.DATASET_META_FNAME:
            log_error(
                'Expected filename {} at {}'.format(
                    DWCA.DATASET_META_FNAME, self.ds_meta_fname), 
                logger=self.logger)
            return ''
        tree = ET.parse(self.ds_meta_fname)
        root = tree.getroot()
        elt = root.find('dataset')
        id_elts = elt.findall('alternateIdentifier')
        for ie in id_elts:
            idstr = ie.text
            if self._is_guid(idstr):
                break
        return idstr
    
    # ......................................................
    def _fix_char(self, ch):
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
    def read_core_fileinfo(self):
        """Reads meta.xml file for information about the core occurrence file
        
        Returns:
            Dictionary of core occurrence file information, with keys matching the 
            names/tags in the meta.xml file:
                location (for filename), id (for fieldname of record UUID) 
                fieldsTerminatedBy, linesTerminatedBy, fieldsEnclosedBy, 
            plus: 
                fieldnames: ordered fieldnames 
                fieldname_index_map: dict of fields and corresponding column indices
        """
        if os.path.split(self.meta_fname)[1] != DWCA.META_FNAME:
            log_error(
                'Expected filename {} at {}'.format(
                    DWCA.META_FNAME, self.meta_fname), logger=self.logger)
            return ''
        fileinfo = {}
        field_idxs = {}
        tree = ET.parse(self.meta_fname)
        root = tree.getroot()
        core_elt = root.find('{}core'.format(DWCA.NS))
        if core_elt.attrib['rowType'] == DWCA.CORE_TYPE:
            # CSV file name
            core_files_elt = core_elt.find('{}files'.format(DWCA.NS))
            core_loc_elt = core_files_elt.find('{}{}'.format(DWCA.NS, DWCA.LOCATION_KEY))
            fileinfo[DWCA.LOCATION_KEY] = core_loc_elt.text
            # CSV file structure
            fileinfo[DWCA.DELIMITER_KEY] = self._fix_char(
                core_elt.attrib[DWCA.DELIMITER_KEY])
            fileinfo[DWCA.LINE_DELIMITER_KEY] = self._fix_char(
                core_elt.attrib[DWCA.LINE_DELIMITER_KEY])
            quote_char = self._fix_char(
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
            all_idxs = set([int(uuid_idx)])
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
                    field_idxs.pop(DWCA.UUID_KEY)
                all_idxs.add(int(idx))
                field_idxs[idx] = term
                field_idxs[term] = idx
            fileinfo[DWCA.UUID_KEY] = uuid_fldname
            fileinfo[DWCA.FLDMAP_KEY] = field_idxs
            # CSV file fieldnames ordered by column index
            all_idxs = list(all_idxs)
            all_idxs.sort()
            ordered_fldnames = []
            for i in all_idxs:
                ordered_fldnames.append(field_idxs[str(i)])
            fileinfo[DWCA.FLDS_KEY] = ordered_fldnames
                
        return fileinfo

