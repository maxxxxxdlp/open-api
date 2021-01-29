"""Module containing functions for API Queries"""
from copy import copy
import csv
import os
import requests
# import idigbio
import urllib

from LmRex.common.lmconstants import (
    BISON, BisonQuery, GBIF, HTTPStatus, Idigbio, Itis, Lifemapper, MorphoSource, 
    DWC, S2N, ServiceProvider, URL_ESCAPES, ENCODING, JSON_HEADERS, TST_VALUES)
from LmRex.fileop.ready_file import ready_filename
from LmRex.fileop.logtools import (log_info, log_warn, log_error)
from LmRex.tools.lm_xml import fromstring, deserialize

# .............................................................................
class APIQuery:
    """Class to query APIs and return results.

    Note:
        CSV files are created with tab delimiter
    """
    DELIMITER = GBIF.DATA_DUMP_DELIMITER
    GBIF_MISSING_KEY = 'unmatched_gbif_ids'

    def __init__(self, base_url, q_key='q', q_filters=None,
                 other_filters=None, filter_string=None, headers=None, 
                 logger=None):
        """
        @summary Constructor for the APIQuery class
        """
        self.logger = logger
        self._q_key = q_key
        self.headers = {} if headers is None else headers
        # No added filters are on url (unless initialized with filters in url)
        self.base_url = base_url
        self._q_filters = {} if q_filters is None else q_filters
        self._other_filters = {} if other_filters is None else other_filters
        self.filter_string = self._assemble_filter_string(
            filter_string=filter_string)
        self.output = None
        self.error = None
        self.debug = False

    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        """
        Standardize record to common schema. 
        
        Note: 
            implemented in subclasses
        """
        raise Exception('Not implemented in base class')
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_key, records_key, record_format, 
            count_only=False, err=None):
        std_output = {S2N.COUNT_KEY: 0}
        errmsgs = []
        stdrecs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        try:
            total = output[count_key]
        except:
            errmsgs.append(cls._get_error_message(
                msg='Missing `{}` element'.format(count_key)))
        else:
            std_output[S2N.COUNT_KEY] = total
        # Records
        if not count_only:
            try:
                recs = output[records_key]
            except:
                errmsgs.append(
                    cls._get_error_message(msg='Missing `{}` element'.format(
                        records_key)))
            else:
                for r in recs:
                    try:
                        stdrecs.append(cls._standardize_record(r))
                    except Exception as e:
                        msg = cls._get_error_message(err=e)
                        errmsgs.append(msg)            
            std_output[S2N.RECORD_FORMAT_KEY] = record_format
            std_output[S2N.RECORDS_KEY] = stdrecs
        # Errors
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output

    # .....................................
    @classmethod
    def _get_error_message(cls, msg=None, err=None):
        text = cls.__name__
        if msg is not None:
            text = '{}; {}'.format(text, msg)
        if err is not None:
            text = '{}; (exception: {})'.format(text, err)
        return text
    
    # .....................................
    @classmethod
    def init_from_url(cls, url, headers=None, logger=None):
        """Initialize APIQuery from a url

        Args:
            url (str): The url to use as the base
            headers (dict): Headers to use for query
        """
        if headers is None:
            headers = {}
        base, filters = url.split('?')
        qry = APIQuery(
            base, filter_string=filters, headers=headers, logger=logger)
        return qry

    # .........................................
    @property
    def url(self):
        """Retrieve a url for the query"""
        # All filters added to url
        if self.filter_string and len(self.filter_string) > 1:
            return '{}?{}'.format(self.base_url, self.filter_string)

        return self.base_url

    # ...............................................
    def add_filters(self, q_filters=None, other_filters=None):
        """Add or replace filters.

        Note:
            This does not remove existing filters unless they are replaced
        """
        self.output = None
        q_filters = {} if q_filters is None else q_filters
        other_filters = {} if other_filters is None else other_filters

        for k, val in q_filters.items():
            self._q_filters[k] = val
        for k, val in other_filters.items():
            self._other_filters[k] = val
        self.filter_string = self._assemble_filter_string()

    # ...............................................
    def clear_all(self, q_filters=True, other_filters=True):
        """Clear existing q_filters, other_filters, and output
        """
        self.output = None
        if q_filters:
            self._q_filters = {}
        if other_filters:
            self._other_filters = {}
        self.filter_string = self._assemble_filter_string()

    # ...............................................
    def clear_other_filters(self):
        """Clear existing otherFilters and output
        """
        self.clear_all(other_filters=True, q_filters=False)

    # ...............................................
    def clear_q_filters(self):
        """Clear existing qFilters and output
        """
        self.clear_all(other_filters=False, q_filters=True)

    # ...............................................
    def _burrow(self, key_list):
        this_dict = self.output
        if isinstance(this_dict, dict):
            for key in key_list:
                try:
                    this_dict = this_dict[key]
                except KeyError:
                    raise Exception('Missing key {} in output'.format(key))
        else:
            raise Exception('Invalid output type ({})'.format(type(this_dict)))
        return this_dict


    # ...............................................
    def _assemble_filter_string(self, filter_string=None):
        # Assemble key/value pairs
        if filter_string is None:
            all_filters = self._other_filters.copy()
            if self._q_filters:
                q_val = self._assemble_q_val(self._q_filters)
                all_filters[self._q_key] = q_val
            for k, val in all_filters.items():
                if isinstance(val, bool):
                    val = str(val).lower()
#                 elif isinstance(val, str):
#                     for oldstr, newstr in URL_ESCAPES:
#                         val = val.replace(oldstr, newstr)
                # works for GBIF, iDigBio, ITIS web services (no manual escaping)
                all_filters[k] = str(val).encode(ENCODING)
            filter_string = urllib.parse.urlencode(all_filters)
        # Escape filter string
        else:
            for oldstr, newstr in URL_ESCAPES:
                filter_string = filter_string.replace(oldstr, newstr)

        return filter_string

    # ...............................................
    @classmethod
    def _interpret_q_clause(cls, key, val, logger=None):
        clause = None
        if isinstance(val, (float, int, str)):
            clause = '{}:{}'.format(key, str(val))
        # Tuple for negated or range value
        elif isinstance(val, tuple):
            # negated filter
            if isinstance(val[0], bool) and val[0] is False:
                clause = 'NOT ' + key + ':' + str(val[1])
            # range filter (better be numbers)
            elif isinstance(
                    val[0], (float, int)) and isinstance(val[1], (float, int)):
                clause = '{}:[{} TO {}]'.format(key, str(val[0]), str(val[1]))
            else:
                log_warn('Unexpected value type {}'.format(val), logger=logger)
        else:
            log_warn('Unexpected value type {}'.format(val), logger=logger)
        return clause

    # ...............................................
    def _assemble_q_item(self, key, val):
        itm_clauses = []
        # List for multiple values of same key
        if isinstance(val, list):
            for list_val in val:
                itm_clauses.append(self._interpret_q_clause(key, list_val))
        else:
            itm_clauses.append(self._interpret_q_clause(key, val))
        return itm_clauses

    # ...............................................
    def _assemble_q_val(self, q_dict):
        clauses = []
        q_val = ''
        # interpret dictionary
        for key, val in q_dict.items():
            clauses.extend(self._assemble_q_item(key, val))
        # convert to string
        first_clause = ''
        for cls in clauses:
            if not first_clause and not cls.startswith('NOT'):
                first_clause = cls
            elif cls.startswith('NOT'):
                q_val = ' '.join((q_val, cls))
            else:
                q_val = ' AND '.join((q_val, cls))
        q_val = first_clause + q_val
        return q_val

    # ...............................................
    def query_by_get(self, output_type='json'):
        """
        Queries the API and sets 'output' attribute to a JSON or ElementTree 
        object and S2N.ERRORS_KEY attribute to a string if appropriate.
        
        Note:
            Sets a single error message, not a list, to error attribute
        """
        self.output = {}
        self.error = None
        errmsg = None
        try:
            response = requests.get(self.url, headers=self.headers)
        except Exception as e:
            errmsg = self._get_error_message(err=e)
        else:
            if response.status_code == HTTPStatus.OK:
                if output_type == 'json':
                    try:
                        self.output = response.json()
                    except Exception as e:
                        output = response.content
                        if output.find(b'<html') != -1:
                            errmsg = self._get_error_message(
                                msg='Provider error', 
                                err='Invalid JSON output ({})'.format(output))
                        else:
                            try:
                                self.output = deserialize(fromstring(output))
                            except:
                                errmsg = self._get_error_message(
                                    msg='Provider error', err=e)
                elif output_type == 'xml':
                    try:
                        output = fromstring(response.text)
                        self.output = output
                    except Exception as e:
                        self.output = response.text
                else:
                    errmsg = self._get_error_message(
                        msg='Unrecognized output type {}'.format(output_type))
            else:
                errmsg = self._get_error_message(
                    msg='code = {}, reason = {}'.format(
                        response.status_code, response.reason))
        if errmsg:
            self.error = errmsg

    # ...........    ....................................
    def query_by_post(self, output_type='json', file=None):
        """Perform a POST request."""
        self.output = None
        self.error = None
        errmsg = None
        # Post a file
        if file is not None:
            # TODO: send as bytes here?
            files = {'files': open(file, 'rb')}
            try:
                response = requests.post(self.base_url, files=files)
            except Exception as e:
                try:
                    ret_code = response.status_code
                    reason = response.reason
                except Exception:
                    ret_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    reason = 'Unknown Error'
                errmsg = self._get_error_message(
                    msg='file {}, code = {}, reason = {}'.format(
                        file, ret_code, reason),
                    err=e)
        # Post parameters
        else:
            all_params = self._other_filters.copy()
            if self._q_filters:
                all_params[self._q_key] = self._q_filters
            query_as_string = urllib.parse.urlencode(all_params)
            url = self.base_url + '/?' + query_as_string
            try:
                response = requests.post(url, headers=self.headers)
            except Exception as e:
                try:
                    ret_code = response.status_code
                    reason = response.reason
                except Exception:
                    ret_code = HTTPStatus.INTERNAL_SERVER_ERROR
                    reason = 'Unknown Error'
                errmsg = self._get_error_message(
                    msg='code = {}, reason = {}'.format(ret_code, reason), 
                    err=e)

        if response.ok:
            try:
                if output_type == 'json':
                    try:
                        self.output = response.json()
                    except Exception as e:
                        output = response.content
                        self.output = deserialize(fromstring(output))
                elif output_type == 'xml':
                    output = response.text
                    self.output = deserialize(fromstring(output))
                else:
                    errmsg = 'Unrecognized output type {}'.format(output_type)
            except Exception as e:
                errmsg = self._get_error_message(
                    msg='Unrecognized output, URL {}, content={}'.format(
                        self.base_url, response.content),
                    err=e)
        else:
            try:
                ret_code = response.status_code
                reason = response.reason
            except Exception:
                ret_code = HTTPStatus.INTERNAL_SERVER_ERROR
                reason = 'Unknown Error'
            errmsg = self._get_error_message(
                msg='URL {}, code = {}, reason = {}'.format(
                    self.base_url, ret_code, reason))
        if errmsg is not None:
            self.error = errmsg


# .............................................................................
class BisonAPI(APIQuery):
    """Class to query BISON APIs and return results
    OPEN_SEARCH occ
    https://bison.usgs.gov/api/search.json?species=Bison%20bison&type=scientific_name&start=0&count=1000
    WMS map
    https://bison.usgs.gov/api/wms?LAYERS=species&species=Bison%20bison&type=scientific_name&TRANSPARENT=true&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&SRS=EPSG%3A3857&BBOX=-20037508.34,-1.862645149231e-9,-5009377.085,15028131.255&WIDTH=512&HEIGHT=512    
    """
    PROVIDER = ServiceProvider.BISON['name']
    # ...............................................
    def __init__(
            self, url=BISON.SOLR_URL, q_filters=None, other_filters=None, 
            extended_params=None, filter_string=None, headers=None, logger=None):
        """Constructor for BisonAPI class"""
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        if url == BISON.OPEN_SEARCH_URL:
            pairs = []
            for k, v in extended_params.items():
                if isinstance(v, list) or isinstance(v, tuple):
                    val = ''
                    for opt in v:
                        val = '{} "{}"'.format(val, opt)
                        pairs.append('{}=({})'.format(k, val))
                else:
                    pairs.append('{}=({})'.format(k, v))
        elif url == BISON.SOLR_URL:
            all_q_filters = copy(BisonQuery.QFILTERS)
            if q_filters:
                all_q_filters.update(q_filters)
     
            # Add/replace other filters to defaults for this instance
            all_other_filters = copy(BisonQuery.FILTERS)
            if other_filters:
                all_other_filters.update(other_filters)
     
            APIQuery.__init__(
                self, BISON.SOLR_URL, q_key='q', q_filters=all_q_filters,
                other_filters=all_other_filters, filter_string=filter_string,
                headers=headers, logger=logger)

    # ...............................................
    def query(self):
        """Queries the API and sets 'output' attribute to a JSON object"""
        APIQuery.query_by_get(self, output_type='json')
        # TODO: Test for expected content

    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def get_occurrences_by_name(cls, namestr, count_only, logger=None):
        """
        Get or count records for the given namestr.
        
        Args:
            dataset_key: unique identifier for the dataset, assigned by GBIF
                and retained by Specify
            count_only: boolean flag signaling to return records or only count
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning, info
        
        Todo: 
            handle large queries asynchronously
        """
        if count_only is True:
            limit = 1
        else:
            limit = BISON.LIMIT
        ofilters = {
            'species': namestr, 'type': 'scientific_name', 'start': 0, 
            S2N.COUNT_KEY: limit}

        api = BisonAPI(
            url=BISON.OPEN_SEARCH_URL, other_filters=ofilters, logger=logger)
        qry_meta = {
            S2N.NAME_KEY: namestr, S2N.PROVIDER_KEY: cls.PROVIDER, 
            S2N.PROVIDER_QUERY_KEY: [api.url]}

        try:
            api.query_by_get()
        except Exception as e:
            std_output = {S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            std_output = cls._standardize_output(
                api.output, BISON.COUNT_KEY, BISON.RECORDS_KEY, 
                BISON.RECORD_FORMAT, count_only=count_only, err=api.error)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val             
        return std_output                
        
#     # ...............................................
#     @classmethod
#     def get_tsn_list_for_binomials(cls, logger=None):
#         """Returns a list of sequences containing tsn and tsnCount"""
#         bison_qry = BisonAPI(
#             q_filters={BISON.NAME_KEY: BISON.BINOMIAL_REGEX},
#             other_filters=BisonQuery.TSN_FILTERS, logger=logger)
#         tsn_list = bison_qry._get_binomial_tsns()
#         return tsn_list
# 
#     # ...............................................
#     def _get_binomial_tsns(self):
#         data_list = None
#         self.query()
#         if self.output is not None:
#             data_count = self._burrow(BisonQuery.COUNT_KEYS)
#             data_list = self._burrow(BisonQuery.TSN_LIST_KEYS)
#             log_info(
#                 'Reported count = {}, actual count = {}'.format(
#                     data_count, len(data_list)), 
#                 logger=self.logger)
#         return data_list
# 
#     # ...............................................
#     @classmethod
#     def get_itis_tsn_values(cls, itis_tsn, logger=None):
#         """Return ItisScientificName, kingdom, and TSN info for occ record"""
#         itis_name = king = tsn_hier = None
#         try:
#             occ_api = BisonAPI(
#                 q_filters={BISON.HIERARCHY_KEY: '*-{}-'.format(itis_tsn)},
#                 other_filters={'rows': 1}, logger=logger)
#             tsn_hier = occ_api.get_first_value_for(BISON.HIERARCHY_KEY)
#             itis_name = occ_api.get_first_value_for(BISON.NAME_KEY)
#             king = occ_api.get_first_value_for(BISON.KINGDOM_KEY)
#         except Exception as e:
#             log_error(str(e))
#             raise
#         return (itis_name, king, tsn_hier)
# 
#     # ...............................................
#     def get_tsn_occurrences(self):
#         """Returns a list of occurrence record dictionaries"""
#         data_list = []
#         if self.output is None:
#             self.query()
#         if self.output is not None:
#             data_list = self._burrow(BisonQuery.RECORD_KEYS)
#         return data_list
# 
#     # ...............................................
#     def get_first_value_for(self, field_name):
#         """Returns first value for given field name"""
#         val = None
#         records = self.get_tsn_occurrences()
#         for rec in records:
#             try:
#                 val = rec[field_name]
#                 break
#             except KeyError:
#                 log_error(
#                     'Missing {} for {}'.format(field_name, self.url), 
#                     logger=self.logger)
#         return val


# .............................................................................
class ItisAPI(APIQuery):
    """Class to pull data from the ITIS Solr or Web service, documentation at:
        https://www.itis.gov/solr_documentation.html and 
        https://www.itis.gov/web_service.html
    """
    PROVIDER = ServiceProvider.ITISSolr['name']
    # ...............................................
    def __init__(
            self, base_url, service=None, q_filters={}, other_filters={}, 
            logger=None):
        """Constructor for ItisAPI class.
        
        Args:
            base_url: Base URL for the ITIS Solr or Web service
            service: Indicator for which ITIS Web service to address
            q_filters:
            other_filters:
            
        Note:
            ITIS Solr service does not have nested services
        """
        if base_url == Itis.SOLR_URL:
            other_filters['wt'] = 'json'
        if service is not None:
            base_url = '{}/{}'.format(base_url, service)
        APIQuery.__init__(
            self, base_url, q_filters=q_filters, other_filters=other_filters,
            logger=logger)

    # ...............................................
    def _assemble_filter_string(self, filter_string=None):
        # Assemble key/value pairs
        if filter_string is None:
            all_filters = self._other_filters.copy()
            if self._q_filters:
                q_val = self._assemble_q_val(self._q_filters)
                all_filters[self._q_key] = q_val

            if self.base_url == Itis.SOLR_URL:
                kvpairs = []
                for k, val in all_filters.items():
                    if isinstance(val, bool):
                        val = str(val).lower()
                    # manual escaping for ITIS Solr
                    elif isinstance(val, str):
                        for oldstr, newstr in URL_ESCAPES:
                            val = val.replace(oldstr, newstr)
                    kvpairs.append('{}={}'.format(k, val))
                filter_string = '&'.join(kvpairs)
            else:
                for k, val in all_filters.items():
                    if isinstance(val, bool):
                        val = str(val).lower()
                # urlencode for ITIS web services
                filter_string = urllib.parse.urlencode(all_filters)
            
        # Escape filter string
        else:
            for oldstr, newstr in URL_ESCAPES:
                filter_string = filter_string.replace(oldstr, newstr)
        return filter_string  

    # ...............................................
    def _processRecordInfo(self, rec, header, reformat_keys=[]):
        row = []
        if rec is not None:
            for key in header:
                try:
                    val = rec[key]
                    
                    if type(val) is list:
                        if len(val) > 0:
                            val = val[0]
                        else:
                            val = ''
                            
                    if key in reformat_keys:
                        val = self._saveNLDelCR(val)
                        
                    elif key == 'citation':
                        if type(val) is dict:
                            try:
                                val = val['text']
                            except:
                                pass
                        
                    elif key in ('created', 'modified'):
                        val = self._clipDate(val)
                            
                except KeyError:
                    val = ''
                row.append(val)
        return row

# ...............................................
    @classmethod
    def _get_fld_value(cls, doc, fldname):
        try:
            val = doc[fldname]
        except:
            val = None
        return val

    # ...............................................
    @classmethod
    def _get_rank_from_path(cls, tax_path, rank_key):
        for rank, tsn, name in tax_path:
            if rank == rank_key:
                return (int(tsn), name)
        return (None, None)

    # ...............................................
    def _return_hierarchy(self):
        """
        Todo:
            Look at formatted strings, I don't know if this is working
        """
        tax_path = []
        for tax in self.output.iter(
                # '{{}}{}'.format(Itis.DATA_NAMESPACE, Itis.HIERARCHY_TAG)):
                '{}{}'.format(Itis.DATA_NAMESPACE, Itis.HIERARCHY_TAG)):
            rank = tax.find(
                # '{{}}{}'.format(Itis.DATA_NAMESPACE, Itis.RANK_TAG)).text
                '{}{}'.format(Itis.DATA_NAMESPACE, Itis.RANK_TAG)).text
            name = tax.find(
                # '{{}}{}'.format(Itis.DATA_NAMESPACE, Itis.TAXON_TAG)).text
                '{}{}'.format(Itis.DATA_NAMESPACE, Itis.TAXON_TAG)).text
            tsn = tax.find(
                # '{{}}{}'.format(Itis.DATA_NAMESPACE, Itis.TAXONOMY_KEY)).text
                '{}{}'.format(Itis.DATA_NAMESPACE, Itis.TSN_KEY)).text
            tax_path.append((rank, tsn, name))
        return tax_path

# ...............................................
    @classmethod
    def _get_itis_solr_recs(cls, itis_output):
        std_output = {}
        errmsgs = []
        try:
            data = itis_output['response']
        except:
            errmsgs.append(cls._get_error_message(
                msg='Missing `response` element'))
        else:
            try:
                std_output[S2N.COUNT_KEY] = data['numFound']
            except:
                errmsgs.append(cls._get_error_message(
                    msg='Missing `count` element'))
            try:
                std_output[S2N.RECORDS_KEY] = data['docs']
            except:
                errmsgs.append(cls._get_error_message(
                    msg='Missing `docs` element'))
        if errmsgs:
            std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output
            
    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_key, records_key, record_format, 
            itis_accepted=False, count_only=False, err=None):
        std_output = {S2N.COUNT_KEY: 0}
        stdrecs = []
        errmsgs = []
        if err is not None:
            errmsgs.append(err)

        try:
            std_output[S2N.COUNT_KEY] = output[count_key]
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        try:
            docs = output[records_key]
        except:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            for doc in docs:
                if itis_accepted is False:
                    stdrecs.append(cls._standardize_record(doc))
                else:
                    usage = doc['usage'].lower()
                    if usage in ('accepted', 'valid'):
                        stdrecs.append(cls._standardize_record(doc))
        std_output[S2N.RECORD_FORMAT_KEY] = record_format
        std_output[S2N.RECORDS_KEY] = stdrecs
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output
    
# ...............................................
    @classmethod
    def match_name(cls, sciname, itis_accepted=None, kingdom=None, logger=None):
        """Return an ITIS record for a scientific name using the 
        ITIS Solr service.
        
        Args:
            sciname: a scientific name designating a taxon
            status: optional designation for taxon status, 
                kingdom Plantae are valid/invalid, others are accepted 
            kingdom: optional designation for kingdom
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning
            
        Example URL: 
            http://services.itis.gov/?q=nameWOInd:Spinus\%20tristis&wt=json
        """
        q_filters = {Itis.NAME_KEY: sciname}
        if kingdom is not None:
            q_filters['kingdom'] = kingdom
        api = ItisAPI(Itis.SOLR_URL, q_filters=q_filters, logger=logger)
        qry_meta = {
            S2N.NAME_KEY: sciname, S2N.PROVIDER_KEY: cls.PROVIDER, 
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        
        try:
            api.query()
        except Exception as e:
            std_output = {S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            try:
                output = api.output['response']
            except Exception as e:
                if api.error is not None:
                    std_output = {S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [api.error]}
                else:
                    std_output = {
                        S2N.COUNT_KEY: 0, 
                        S2N.ERRORS_KEY: [cls._get_error_message(
                            msg='Missing `response` element')]}
            else:
                # Standardize output from provider response
                std_output = cls._standardize_output(
                    output, Itis.COUNT_KEY, Itis.RECORDS_KEY, Itis.RECORD_FORMAT, 
                    itis_accepted=itis_accepted, err=api.error)

        # Add query parameters to output
        for k, v in qry_meta.items():
            std_output[k] = v
        return std_output
    
# ...............................................
    @classmethod
    def match_name_nonsolr(cls, sciname, count_only=False, outformat='json', logger=None):
        """Return matching names for scienfific name using the ITIS Web service.
        
        Args:
            sciname: a scientific name
            
        Ex: https://services.itis.gov/?q=tsn:566578&wt=json
        """
        output = {}
        errmsgs = []
        if outformat == 'json':
            url = Itis.JSONSVC_URL
        else:
            url = Itis.WEBSVC_URL
            outformat = 'xml'
        apiq = ItisAPI(
            url, service=Itis.ITISTERMS_FROM_SCINAME_QUERY, 
            other_filters={Itis.SEARCH_KEY: sciname}, logger=logger)
        apiq.query_by_get(output_type=outformat)
        
        recs = []
        if outformat == 'json':    
            outjson = apiq.output
            try:
                recs = outjson['itisTerms']
            except:
                errmsgs.append(cls._get_error_message(
                    msg='Missing `itisTerms` element'))
        else:
            root = apiq.output    
            retElt = root.find('{}return'.format(Itis.NAMESPACE))
            if retElt is not None:
                termEltLst = retElt.findall('{}itisTerms'.format(Itis.DATA_NAMESPACE))
                for tElt in termEltLst:
                    rec = {}
                    elts = tElt.getchildren()
                    for e in elts:
                        rec[e.tag] = e.text
                    if rec:
                        recs.append(rec)
                        
        output[S2N.COUNT_KEY] = len(recs)
        if not count_only:
            output[S2N.RECORDS_KEY] = recs
            output[S2N.RECORD_FORMAT_KEY] = 'tbd'
        output[S2N.ERRORS_KEY] = errmsgs
        return output

# ...............................................
    @classmethod
    def get_name_by_tsn(cls, tsn, logger=None):
        """Return a name and kingdom for an ITIS TSN using the ITIS Solr service.
        
        Args:
            tsn: a unique integer identifier for a taxonomic record in ITIS
            
        Ex: https://services.itis.gov/?q=tsn:566578&wt=json
        """
        output = {}
        apiq = ItisAPI(
            Itis.SOLR_URL, q_filters={Itis.TSN_KEY: tsn}, logger=logger)
        docs = apiq.get_itis_recs()
        recs = []
        for doc in docs:
            usage = doc['usage']
            if usage in ('accepted', 'valid'):
                recs.append(doc)
        output[S2N.COUNT_KEY] = len(recs)
        output[S2N.RECORDS_KEY] = recs
        return output

# # ...............................................
#     @classmethod
#     def get_vernacular_by_tsn(cls, tsn, logger=None):
#         """Return vernacular names for an ITIS TSN.
#         
#         Args:
#             tsn: an ITIS code designating a taxonomic name
#         """
#         common_names = []
#         if tsn is not None:
#             url = '{}/{}?{}={}'.format(
#                 Itis.WEBSVC_URL, Itis.VERNACULAR_QUERY, Itis.TSN_KEY, str(tsn))
#             root = self._getDataFromUrl(url, resp_type='xml')
#         
#             retElt = root.find('{}return'.format(Itis.NAMESPACE))
#             if retElt is not None:
#                 cnEltLst = retElt.findall('{}commonNames'.format(Itis.DATA_NAMESPACE))
#                 for cnElt in cnEltLst:
#                     nelt = cnElt.find('{}commonName'.format(Itis.DATA_NAMESPACE))
#                     if nelt is not None and nelt.text is not None:
#                         common_names.append(nelt.text)
#         return common_names

    # ...............................................
    @classmethod
    def get_tsn_hierarchy(cls, tsn, logger=None):
        """Retrieve taxon hierarchy"""
        url = '{}/{}'.format(Itis.WEBSVC_URL, Itis.TAXONOMY_HIERARCHY_QUERY)
        apiq = APIQuery(
            url, other_filters={Itis.TSN_KEY: tsn}, 
            headers={'Content-Type': 'text/xml'}, logger=logger)
        apiq.query_by_get(output_type='xml')
        tax_path = apiq._return_hierarchy()
        hierarchy = {}
        for rank in (
                Itis.KINGDOM_KEY, Itis.PHYLUM_DIVISION_KEY, Itis.CLASS_KEY,
                Itis.ORDER_KEY, Itis.FAMILY_KEY, Itis.GENUS_KEY,
                Itis.SPECIES_KEY):
            hierarchy[rank] = apiq._get_rank_from_path(tax_path, rank)
        return hierarchy

    # ...............................................
    def query(self):
        """Queries the API and sets 'output' attribute to a ElementTree object"""
        APIQuery.query_by_get(self, output_type='json')


# .............................................................................
class GbifAPI(APIQuery):
    """Class to query GBIF APIs and return results"""
    PROVIDER = ServiceProvider.GBIF['name']
    # ...............................................
    def __init__(self, service=GBIF.SPECIES_SERVICE, key=None,
                 other_filters=None, logger=None):
        """
        Constructor for GbifAPI class
        
        Args:
            service: GBIF service to query
            key: unique identifier for an object of this service
            other_filters: optional filters
            logger: optional logger for info and error messages.  If None, 
                prints to stdout
        """
        url = '/'.join((GBIF.REST_URL, service))
        if key is not None:
            url = '/'.join((url, str(key)))
        APIQuery.__init__(self, url, other_filters=other_filters, logger=logger)

    # ...............................................
    def _assemble_filter_string(self, filter_string=None):
        # Assemble key/value pairs
        if filter_string is None:
            all_filters = self._other_filters.copy()
            if self._q_filters:
                q_val = self._assemble_q_val(self._q_filters)
                all_filters[self._q_key] = q_val
            for k, val in all_filters.items():
                if isinstance(val, bool):
                    val = str(val).lower()
                # works for GBIF, iDigBio, ITIS web services (no manual escaping)
                all_filters[k] = str(val).encode(ENCODING)
            filter_string = urllib.parse.urlencode(all_filters)
        # Escape filter string
        else:
            for oldstr, newstr in URL_ESCAPES:
                filter_string = filter_string.replace(oldstr, newstr)
        return filter_string

    # ...............................................
    @classmethod
    def _get_output_val(cls, out_dict, name):
        try:
            tmp = out_dict[name]
            val = str(tmp).encode(ENCODING)
        except Exception:
            return None
        return val

    # ...............................................
    @classmethod
    def get_taxonomy(cls, taxon_key, logger=None):
        """Return GBIF backbone taxonomy for this GBIF Taxon ID
        """
        std_output = {S2N.COUNT_KEY: 0}
        errmsgs = []
        std_recs = []
        rec = {}
        tax_api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key=taxon_key, logger=logger)
        try:
            tax_api.query()
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            output = tax_api.output
            elements_of_interest = [
                'scientificName', 'kingdom', 'phylum', 'class', 'order', 
                'family', 'genus', 'species', 'rank', 'genusKey', 'speciesKey', 
                'taxonomicStatus', 'canonicalName', 'scientificName', 'kingdom', 
                'phylum', 'class', 'order', 'family', 'genus', 'species', 
                'rank', 'genusKey', 'speciesKey', 'taxonomicStatus', 
                'canonicalName', 'acceptedKey', 'accepted', 'nubKey']
            for fld in elements_of_interest:
                rec[fld] = tax_api._get_output_val(output, fld)
            std_recs.append(rec)
            
        std_output[S2N.RECORDS_KEY] = std_recs
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output

    # ...............................................
    @classmethod
    def get_occurrences_by_occid(cls, occid, count_only=False, logger=None):
        """Return GBIF occurrences for this occurrenceId.  This should retrieve 
        a single record if the occurrenceId is unique.
        
        Args:
            occid: occurrenceID for query
            count_only: boolean flag signaling to return records or only count
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning
                
        Todo: enable paging
        """
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={'occurrenceID': occid}, logger=logger)
        qry_meta = {
            S2N.OCCURRENCE_ID_KEY: occid, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        try:
            api.query()
        except Exception as e:
            std_output = {S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            # Standardize output from provider response
            std_output = cls._standardize_output(
                api.output, GBIF.COUNT_KEY, GBIF.RECORDS_KEY, 
                GBIF.RECORD_FORMAT_OCCURRENCE, count_only=count_only, 
                err=api.error)
        # Add query parameters to output
        for k, v in qry_meta.items():
            std_output[k] = v
        return std_output

    # ...............................................
    @classmethod
    def _get_fld_vals(cls, big_rec):
        rec = {}
        for fld_name in GbifAPI.NameMatchFieldnames:
            try:
                rec[fld_name] = big_rec[fld_name]
            except KeyError:
                pass
        return rec

    # ...............................................
    @classmethod
    def _standardize_gbif_occurrence(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_gbif_name(cls, rec):
        # todo: standardize gbif output
        return rec
    
    # ...............................................
    @classmethod
    def _test_record(cls, status, rec):
        is_good = False
        # No filter by status, take original
        if status is None:
            is_good = True
        else:
            outstatus = None
            try:
                outstatus = rec['status'].lower()
            except AttributeError:
                print(cls._get_error_message(msg='No status in record'))
            else:
                if outstatus == status:
                    is_good = True
        return is_good
        
    # ...............................................
    @classmethod
    def _standardize_match_output(cls, output, status, err=None):
            # Pull alternatives out of record
        std_output = {}
        stdrecs = []
        errmsgs = []
        if err:
            errmsgs.append(err)
        try:
            alternatives = output.pop('alternatives')
        except:
            alternatives = []
            
        is_match = True
        try:
            if output['matchType'].lower() == 'none':
                is_match = False
        except AttributeError:
            errmsgs.append(cls._get_error_message(msg='No matchType'))
        else:
            goodrecs = []
            # take primary output if matched
            if is_match:
                if cls._test_record(status, output):
                    goodrecs.append(output)
            for alt in alternatives:
                if cls._test_record(status, alt):
                    goodrecs.append(alt)
            # Standardize name output
            for r in goodrecs:
                stdrecs.append(cls._standardize_gbif_name(r))
        std_output[S2N.COUNT_KEY] = len(stdrecs)
        # TODO: standardize_record and provide schema link
        std_output[S2N.RECORD_FORMAT_KEY] = GBIF.RECORD_FORMAT_NAME
        std_output[S2N.RECORDS_KEY] = stdrecs
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output
        
    # ...............................................
    @classmethod
    def _standardize_record(cls, rec, record_format):
        # todo: standardize gbif output to DWC, DSO, etc
        if record_format == GBIF.RECORD_FORMAT_OCCURRENCE:
            return cls._standardize_gbif_occurrence(rec)
        else:
            return cls._standardize_gbif_name(rec)
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_key, records_key, record_format, count_only=False, err=None):
        std_output = {S2N.COUNT_KEY: 0}
        stdrecs = []
        errmsgs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        try:
            total = output[count_key]
        except:
            errmsgs.append(
                cls._get_error_message(
                    msg='Missing `{}` element'.format(count_key)))
        else:
            std_output[S2N.COUNT_KEY] = total
        # Records
        if not count_only:
            try:
                recs = output[records_key]
            except:
                errmsgs.append(
                    cls._get_error_message(
                        msg='Missing `{}` element'.format(records_key)))
            else:
                stdrecs = []
                for r in recs:
                    try:
                        stdrecs.append(
                            cls._standardize_record(r, record_format))
                    except Exception as e:
                        msg = cls._get_error_message(err=e)
                        errmsgs.append(msg)
            std_output[S2N.RECORDS_KEY] = stdrecs
            std_output[S2N.RECORD_FORMAT_KEY] = record_format
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output
    
    # ...............................................
    @classmethod
    def get_occurrences_by_dataset(
            cls, dataset_key, count_only, logger=None):
        """
        Count and optionally return (a limited number of) records with the given 
        dataset_key.
        
        Args:
            dataset_key: unique identifier for the dataset, assigned by GBIF
                and retained by Specify
            count_only: boolean flag signaling to return records or only count
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning
        
        Todo: 
            handle large queries asynchronously
        """
        if count_only is True:
            limit = 1
        else:
            limit = GBIF.LIMIT   
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={
                'dataset_key': dataset_key, 'offset': 0, 
                'limit': limit}, logger=logger)
        qry_meta = {
            S2N.DATASET_ID_KEY: dataset_key, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        try:
            api.query()
        except Exception as e:
            std_output = {S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            # Standardize output from provider response
            std_output = cls._standardize_output(
                api.output, GBIF.COUNT_KEY, GBIF.RECORDS_KEY, 
                GBIF.RECORD_FORMAT_OCCURRENCE, count_only=count_only, 
                err=api.error)
            
        # Add query parameters to output
        for k, v in qry_meta.items():
            std_output[k] = v
        return std_output


    # ...............................................
    @classmethod
    def match_name(cls, name_str, status=None, logger=None):
        """Return closest accepted species in GBIF backbone taxonomy,
        
        Args:
            name_str: A scientific namestring possibly including author, year, 
                rank marker or other name information.
            status: optional constant to match the TaxonomicStatus in the GBIF
                record
                
        Returns:
            Either a dictionary containing a matching record with status 
                'accepted' or 'synonym' without 'alternatives'.  
            Or, if there is no matching record, return the first/best 
                'alternative' record with status 'accepted' or 'synonym'.

        Note:
            This function uses the name search API, 
        """
        name_clean = name_str.strip()
        other_filters = {'name': name_clean, 'verbose': 'true'}
#         if rank:
#             other_filters['rank'] = rank
#         if kingdom:
#             other_filters['kingdom'] = kingdom
        api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key='match',
            other_filters=other_filters, logger=logger)
        qry_meta = {
            S2N.NAME_KEY: name_clean, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        
        try:
            api.query()
        except Exception as e:
            std_output = {
                S2N.COUNT_KEY: 0, 
                S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            # Standardize output from provider response
            std_output = cls._standardize_match_output(
                api.output, status, err=api.error)
        # Add query parameters to output
        for k, v in qry_meta.items():
            std_output[k] = v
        return std_output


    # ...............................................
    @classmethod
    def count_occurrences_for_taxon(cls, taxon_key, logger=None):
        """Return a count of occurrence records in GBIF with the indicated taxon.
                
        Args:
            taxon_key: A GBIF unique identifier indicating a taxon object.
                
        Returns:
            A record as a dictionary containing the record count of occurrences
            with this accepted taxon, and a URL to retrieve these records.            
        """
        std_output = {S2N.COUNT_KEY: 0}
        errmsgs = []
        # Query GBIF
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={'taxonKey': taxon_key}, logger=logger)
        qry_meta = {
            'taxon_key': taxon_key, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        
        try:
            api.query_by_get()
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            try:
                std_output[S2N.COUNT_KEY] = api.output['count']
            except Exception as e:
                errmsgs.append(cls._get_error_message(
                    msg='Missing `count` element'))
            else:
                if std_output[S2N.COUNT_KEY] < 1:
                    errmsgs.append(cls._get_error_message(msg='No match'))
                std_output['occurrence_url'] = '{}/{}'.format(
                    GBIF.SPECIES_URL, taxon_key)
        # Add query parameters to output
        for k, v in qry_meta.items():
            std_output[k] = v
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output

    # ......................................
    @classmethod
    def _post_json_to_parser(cls, url, data, logger=None):
        response = output = None
        try:
            response = requests.post(url, json=data)
        except Exception as e:
            if response is not None:
                ret_code = response.status_code
            else:
                log_error('Failed on URL {} ({})'.format(url, str(e)), 
                          logger=logger)
        else:
            if response.ok:
                try:
                    output = response.json()
                except Exception as e:
                    try:
                        output = response.content
                    except Exception:
                        output = response.text
                    else:
                        log_error(
                            'Failed to interpret output of URL {} ({})'.format(
                                url, str(e)), logger=logger)
            else:
                try:
                    ret_code = response.status_code
                    reason = response.reason
                except AttributeError:
                    log_error(
                        'Failed to find failure reason for URL {} ({})'.format(
                            url, str(e)), logger=logger)
                else:
                    log_error(
                        'Failed on URL {} ({}: {})'.format(url, ret_code, reason), 
                        logger=logger)
        return output
    
    
# ...............................................
    @classmethod
    def _trim_parsed_output(cls, output, logger=None):
        recs = []
        for rec in output:
            # Only return parsed records
            try:
                success = rec['parsed']
            except:
                log_error('Missing `parsed` field in record', logger=logger)
            else:
                if success:
                    recs.append(rec)
        return recs

# ...............................................
    @classmethod
    def parse_name(cls, namestr, logger=None):
        """
        Send a scientific name to the GBIF Parser returning a canonical name.
        
        Args:
            namestr: A scientific namestring possibly including author, year, 
                rank marker or other name information.
                
        Returns:
            A dictionary containing a single record for a parsed scientific name
            and any optional error messages.
            
        sent (bad) http://api.gbif.org/v1/parser/name?name=Acer%5C%2520caesium%5C%2520Wall.%5C%2520ex%5C%2520Brandis
        send good http://api.gbif.org/v1/parser/name?name=Acer%20heldreichii%20Orph.%20ex%20Boiss.
        """
        output = {}
        # Query GBIF
        name_api = GbifAPI(
            service=GBIF.PARSER_SERVICE, 
            other_filters={GBIF.REQUEST_NAME_QUERY_KEY: namestr},
            logger=logger)
        name_api.query_by_get()
        # Parse results (should be only one)
        if name_api.output is not None:
            recs = name_api._trim_parsed_output(name_api.output)
            try:
                output['record'] = recs[0]
            except:
                msg = 'Failed to return results from {}, ({})'.format(
                    name_api.url, cls.__class__.__name__)
                log_error(msg, logger=logger)
                output[S2N.ERRORS_KEY] = msg
        return output

    # ...............................................
    @classmethod
    def parse_names(cls, names=[], filename=None, logger=None):
        """
        Send a list or file (or both) of scientific names to the GBIF Parser,
        returning a dictionary of results.  Each scientific name can possibly 
        include author, year, rank marker or other name information.
        
        Args:
            names: a list of names to be parsed
            filename: a file of names to be parsed
            
        Returns:
            A list of resolved records, each is a dictionary with keys of 
            GBIF fieldnames and values with field values. 
        """
        if filename and os.path.exists(filename):
            with open(filename, 'r', encoding=ENCODING) as in_file:
                for line in in_file:
                    names.append(line.strip())

        url = '{}/{}'.format(GBIF.REST_URL, GBIF.PARSER_SERVICE)
        try:
            output = GbifAPI._post_json_to_parser(url, names, logger=logger)
        except Exception as e:
            log_error(
                'Failed to get response from GBIF for data {}, {}'.format(
                    filename, e), logger=logger)
            raise e

        if output:
            recs = GbifAPI._trim_parsed_output(output, logger=logger)
            if filename is not None:
                log_info(
                    'Wrote {} parsed records from GBIF to file {}'.format(
                        len(recs), filename), logger=logger)
            else:
                log_info(
                    'Found {} parsed records from GBIF for {} names'.format(
                        len(recs), len(names)), logger=logger)

        return recs

    # ...............................................
    @classmethod
    def get_publishing_org(cls, pub_org_key, logger=None):
        """Return title from one organization record with this key

        Args:
            pub_org_key: GBIF identifier for this publishing organization
        """
        org_api = GbifAPI(
            service=GBIF.ORGANIZATION_SERVICE, key=pub_org_key, logger=logger)
        try:
            org_api.query()
            pub_org_name = org_api._get_output_val(org_api.output, 'title')
        except Exception as e:
            log_error(str(e), logger=logger)
            raise
        return pub_org_name

    # ...............................................
    def query(self):
        """ Queries the API and sets 'output' attribute to a ElementTree object
        """
        APIQuery.query_by_get(self, output_type='json')


# .............................................................................
class IdigbioAPI(APIQuery):
    """Class to query iDigBio APIs and return results"""
    PROVIDER = ServiceProvider.iDigBio['name']
    # ...............................................
    def __init__(self, q_filters=None, other_filters=None, filter_string=None,
                 headers=None, logger=None):
        """Constructor for IdigbioAPI class
        """
        idig_search_url = '/'.join((
            Idigbio.SEARCH_PREFIX, Idigbio.SEARCH_POSTFIX,
            Idigbio.OCCURRENCE_POSTFIX))
        all_q_filters = {}
        all_other_filters = {}

        if q_filters:
            all_q_filters.update(q_filters)

        if other_filters:
            all_other_filters.update(other_filters)

        APIQuery.__init__(
            self, idig_search_url, q_key=Idigbio.QKEY, q_filters=all_q_filters,
            other_filters=all_other_filters, filter_string=filter_string,
            headers=headers, logger=logger)

    # ...............................................
    @classmethod
    def init_from_url(cls, url, headers=None, logger=None):
        """Initialize from url
        """
        base, filters = url.split('?')
        if base.strip().startswith(Idigbio.SEARCH_PREFIX):
            qry = IdigbioAPI(
                filter_string=filters, headers=headers, logger=logger)
        else:
            raise Exception(
                'iDigBio occurrence API must start with {}' .format(
                    Idigbio.SEARCH_PREFIX))
        return qry

    # ...............................................
    def query(self):
        """Queries the API and sets 'output' attribute to a JSON object
        """
        APIQuery.query_by_post(self, output_type='json')

    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize idigbio output to DWC, DSO, etc
        return rec
     
    # ...............................................
    def query_by_gbif_taxon_id(self, taxon_key):
        """Return a list of occurrence record dictionaries."""
        self._q_filters[Idigbio.GBIFID_FIELD] = taxon_key
        self.query()
        specimen_list = []
        if self.output is not None:
            # full_count = self.output['itemCount']
            for item in self.output[Idigbio.RECORDS_KEY]:
                new_item = item[Idigbio.RECORD_CONTENT_KEY].copy()

                for idx_fld, idx_val in item[Idigbio.RECORD_INDEX_KEY].items():
                    if idx_fld == 'geopoint':
                        new_item['dec_long'] = idx_val['lon']
                        new_item['dec_lat'] = idx_val['lat']
                    else:
                        new_item[idx_fld] = idx_val
                specimen_list.append(new_item)
        return specimen_list

    # ...............................................
    @classmethod
    def get_occurrences_by_occid(cls, occid, count_only=False, logger=None):
        """Return iDigBio occurrences for this occurrenceId.  This will
        retrieve a one or more records with the given occurrenceId.
        
        Todo: enable paging
        """
        qf = {Idigbio.QKEY: 
              '{"' + Idigbio.OCCURRENCEID_FIELD + '":"' + occid + '"}'}
        api = IdigbioAPI(other_filters=qf, logger=logger)
        qry_meta = {
            S2N.OCCURRENCE_ID_KEY: occid, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}

        try:
            api.query()
        except Exception as e:
            std_output = {S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            std_output = cls._standardize_output(
                api.output, Idigbio.COUNT_KEY, Idigbio.RECORDS_KEY, 
                Idigbio.RECORD_FORMAT, count_only=count_only, err=api.error)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
        return std_output

    # ...............................................
    @classmethod
    def _write_idigbio_metadata(cls, orig_fld_names, meta_f_name):
        pass

    # ...............................................
    @classmethod
    def _get_idigbio_fields(cls, rec):
        """Get iDigBio fields
        """
        fld_names = list(rec['indexTerms'].keys())
        # add dec_long and dec_lat to records
        fld_names.extend(['dec_lat', 'dec_long'])
        fld_names.sort()
        return fld_names

#     # ...............................................
#     @classmethod
#     def _count_idigbio_records(cls, gbif_taxon_id):
#         """Count iDigBio records for a GBIF taxon id.
#         """
#         api = idigbio.json()
#         record_query = {
#             'taxonid': str(gbif_taxon_id), 'geopoint': {'type': 'exists'}}
# 
#         try:
#             output = api.search_records(rq=record_query, limit=1, offset=0)
#         except Exception:
#             log_info('Failed on {}'.format(gbif_taxon_id))
#             total = 0
#         else:
#             total = output['itemCount']
#         return total
# 
#     # ...............................................
#     def _get_idigbio_records(self, gbif_taxon_id, fields, writer,
#                              meta_output_file):
#         """Get records from iDigBio
#         """
#         api = idigbio.json()
#         limit = 100
#         offset = 0
#         curr_count = 0
#         total = 0
#         record_query = {'taxonid': str(gbif_taxon_id),
#                         'geopoint': {'type': 'exists'}}
#         while offset <= total:
#             try:
#                 output = api.search_records(
#                     rq=record_query, limit=limit, offset=offset)
#             except Exception:
#                 log_info('Failed on {}'.format(gbif_taxon_id))
#                 total = 0
#             else:
#                 total = output['itemCount']
# 
#                 # First gbifTaxonId where this data retrieval is successful,
#                 # get and write header and metadata
#                 if total > 0 and fields is None:
#                     log_info('Found data, writing data and metadata')
#                     fields = self._get_idigbio_fields(output['items'][0])
#                     # Write header in datafile
#                     writer.writerow(fields)
#                     # Write metadata file with column indices
#                     _meta = self._write_idigbio_metadata(
#                         fields, meta_output_file)
# 
#                 # Write these records
#                 recs = output['items']
#                 curr_count += len(recs)
#                 log_info(('  Retrieved {} records, {} recs starting at {}'.format(
#                     len(recs), limit, offset)))
#                 for rec in recs:
#                     rec_data = rec['indexTerms']
#                     vals = []
#                     for fld_name in fields:
#                         # Pull long, lat from geopoint
#                         if fld_name == 'dec_long':
#                             try:
#                                 vals.append(rec_data['geopoint']['lon'])
#                             except KeyError:
#                                 vals.append('')
#                         elif fld_name == 'dec_lat':
#                             try:
#                                 vals.append(rec_data['geopoint']['lat'])
#                             except KeyError:
#                                 vals.append('')
#                         # or just append verbatim
#                         else:
#                             try:
#                                 vals.append(rec_data[fld_name])
#                             except KeyError:
#                                 vals.append('')
# 
#                     writer.writerow(vals)
#                 offset += limit
#         log_info(('Retrieved {} of {} reported records for {}'.format(
#             curr_count, total, gbif_taxon_id)))
#         return curr_count, fields

    # ...............................................
    def assemble_idigbio_data(
            self, taxon_ids, point_output_file, meta_output_file, 
            missing_id_file=None, logger=None):
        """Assemble iDigBio data dictionary"""
        if not isinstance(taxon_ids, list):
            taxon_ids = [taxon_ids]

        # Delete old files
        for fname in (point_output_file, meta_output_file):
            if os.path.exists(fname):
                log_info(
                    'Deleting existing file {} ...'.format(fname), logger=logger)
                os.remove(fname)

        summary = {self.GBIF_MISSING_KEY: []}

        ready_filename(point_output_file, overwrite=True)
        with open(point_output_file, 'w', encoding=ENCODING, newline='') as csv_f:
            writer = csv.writer(csv_f, delimiter=GbifAPI.DELIMITER)
            fld_names = None
            for gid in taxon_ids:
                # Pull / write field names first time
                pt_count, fld_names = self._get_idigbio_records(
                    gid, fld_names, writer, meta_output_file)

                summary[gid] = pt_count
                if pt_count == 0:
                    summary[self.GBIF_MISSING_KEY].append(gid)

        # get/write missing data
        if missing_id_file is not None and len(
                summary[self.GBIF_MISSING_KEY]) > 0:
            with open(missing_id_file, 'w', encoding=ENCODING) as out_f:
                for gid in summary[self.GBIF_MISSING_KEY]:
                    out_f.write('{}\n'.format(gid))

        return summary

    # ...............................................
    def query_idigbio_data(self, taxon_ids):
        """Query iDigBio for data
        """
        if not isinstance(taxon_ids, list):
            taxon_ids = [taxon_ids]

        summary = {self.GBIF_MISSING_KEY: []}

        for gid in taxon_ids:
            # Pull/write fieldnames first time
            pt_count = self._count_idigbio_records(gid)
            if pt_count == 0:
                summary[self.GBIF_MISSING_KEY].append(gid)
            summary[gid] = pt_count

        return summary

# .............................................................................
class LifemapperAPI(APIQuery):
    """Class to query Lifemapper portal APIs and return results"""
    PROVIDER = ServiceProvider.Lifemapper['name']
    # ...............................................
    def __init__(
            self, resource=Lifemapper.PROJ_RESOURCE, ident=None, command=None,  
            other_filters={}, logger=None):
        """Constructor
        
        Args:
            resource: Lifemapper service to query
            ident: a Lifemapper database key for the specified resource.  If 
                ident is None, list using other_filters
            command: optional 'count' to query with other_filters
            other_filters: optional filters
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    
        """
        url = '{}/{}'.format(Lifemapper.URL, resource)
        if ident is not None:
            url = '{}/{}'.format(url, ident)
            # do not send filters if retrieving a known object
            other_filters = {}
        elif command in Lifemapper.COMMANDS:
            url = '{}/{}'.format(url, command)
        APIQuery.__init__(self, url, other_filters=other_filters, logger=logger)

    
    # ...............................................
    @classmethod
    def _standardize_record(cls, rec, color=None):
        try:
            mapname = rec['map']['mapName']
            url = rec['map']['endpoint']
        except Exception as e:
            msg = 'Failed to retrieve map url from {}, {}'.format(rec, e)
            raise Exception(msg)
        else:
            endpoint = '{}/{}'.format(url, mapname)
            try:
                data_url = rec['spatialRaster']['dataUrl']
            except:
                msg = 'Failed to get projection API link (spatialRaster/dataUrl)'
                raise Exception(msg)
            else:        
                proj_url = data_url.rstrip('/gtiff')
                try:
                    occid = rec['occurrenceSet']['id']
                    point_url = rec['occurrenceSet']['metadataUrl']
                    point_name = 'occ_{}'.format(occid)
                    newrec = {
                        'endpoint': endpoint,
                        'point_link': point_url,
                        'point_name': point_name,
                        'species_name': rec['speciesName'],
                        'modtime': rec['statusModTime'],
                        'projection_link': proj_url}
                except Exception as e:
                    msg = 'Failed to retrieve point data from {}, {}'.format(rec, e)
                    raise Exception(msg)
        
        # Ran the gauntlet of exceptions
        if color is not None:
            newrec['vendor-specific-parameters'] = {'color': color}
        # Minor errors return messages within record
        record_errors = []
        try:
            stat = rec['status']
        except:
            msg = 'Failed to get projection \'status\' for layer {}'.format(
                proj_url)
            record_errors.append(msg)
        else:
            # No projection layer without Complete status 
            if stat == Lifemapper.COMPLETE_STAT_VAL:
                try:
                    newrec['projection_name'] = rec['map']['layerName']
                except:
                    msg = 'Failed to get projection map/layerName from {}'.format(
                        proj_url)
                    record_errors.append(msg)
                # Add projection metadata
                try:
                    prj_metadata = rec['metadata']
                except:
                    msg = 'Failed to retrieve projection metadata for {}'.format(
                        proj_url)
                    record_errors.append(msg)
                for key in Lifemapper.PROJECTION_METADATA_KEYS:
                    try:
                        prj_metadata[key] = rec[key]
                    except:
                        msg = 'Failed to retrieve projection {} for {}'.format(
                            key, proj_url)
                        record_errors.append(msg)
        if len(record_errors) > 0:
            newrec[S2N.ERRORS_KEY] = record_errors
        return newrec
    
    # ...............................................
    @classmethod
    def _standardize_output(cls, output, color=None, count_only=False, err=None):
        stdrecs = []
        errmsgs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        std_output = {S2N.COUNT_KEY: len(output)}
        # Records]
        if not count_only:
            for r in output:
                try:
                    stdrecs.append(cls._standardize_record(r, color=color))
                except Exception as e:
                    errmsgs.append(cls._get_error_message(err=e))
            # TODO: revisit record format for other map providers
            std_output[S2N.RECORD_FORMAT_KEY] = Lifemapper.RECORD_FORMAT_MAP
            std_output[S2N.RECORDS_KEY] = stdrecs
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output
    
#     # ...............................................
#     @classmethod
#     def _construct_map_url(
#             cls, rec, bbox, color, exceptions, height, layers, frmat, request, 
#             srs, transparent, width):
#         """
#         service=wms&request=getmap&version=1.0&srs=epsg:4326&bbox=-180,-90,180,90&format=png&width=600&height=300&layers=prj_1848399
#         """
#         try:
#             mapname = rec['map']['mapName']
#             lyrname = rec['map']['layerName']
#             url = rec['map']['endpoint']
#         except Exception as e:
#             msg = 'Failed to retrieve map data from {}, {}'.format(rec, e)
#             rec = {'spcoco.error': msg}
#         else:
#             tmp = layers.split(',')
#             lyrcodes = [t.strip() for t in tmp]
#             lyrnames = []
#             # construct layers for display from bottom layer up to top: 
#             #     bmng (background image), prj (projection), occ (points)
#             if 'bmng' in lyrcodes:
#                 lyrnames.append('bmng')
#             if 'prj' in lyrcodes:
#                 lyrnames.append(lyrname)
#             if 'occ' in lyrcodes:
#                 try:
#                     occid = rec['occurrenceSet']['id']
#                 except:
#                     msg = 'Failed to retrieve occurrence layername'
#                 else:
#                     occlyrname = 'occ_{}'.format(occid)
#                     lyrnames.append(occlyrname)
#             lyrstr = ','.join(lyrnames)
#             
#             filters = {
#                 'bbox': bbox, 'height': height, 'layers': lyrstr, 
#                 'format': frmat, 'request': request, 'srs': srs, 'width': width}
#             # Optional, LM-specific, filters
#             # TODO: fix color parameter in Lifemapper maps
# #             if color is not None:
# #                 filters['color'] = color 
#             if exceptions is not None:
#                 filters['exceptions'] = exceptions
#             if transparent is not None:
#                 filters['transparent'] = transparent
#                 
#             filter_str = 'service=wms&version=1.0'
#             for (key, val) in filters.items():
#                 filter_str = '{}&{}={}'.format(filter_str, key, val) 
#             map_url = '{}/{}?{}'.format(url, mapname, filter_str)
#         return map_url
# 
#     # ...............................................
#     @classmethod
#     def find_projections_by_name(
#             cls, name, prjscenariocode=None, bbox='-180,-90,180,90', 
#             color=None, exceptions=None, height=300, layers='prj', frmat='png', 
#             request='getmap', srs='epsg:4326',  transparent=None, width=600, 
#             other_filters={}, logger=None):
#         """
#         List projections for a given scientific name.  
#         
#         Args:
#             name: a scientific name 'Accepted' according to the GBIF Backbone 
#                 Taxonomy
#             prjscenariocode: a Lifemapper code indicating whether the 
#                 environmental data used for creating the projection is 
#                 observed, or modeled past or future.  Codes are in 
#                 LmREx.common.lmconstants Lifemapper.*_SCENARIO_CODE*. If the 
#                 code is None, return a map with only occurrence points
#             logger: optional logger for info and error messages.  If None, 
#                 prints to stdout    
# 
#         Note: 
#             Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
#             Taxonomy and this method requires them for success.
# 
#         Todo:
#             handle full record returns instead of atoms
#         """
#         output = {}
#         recs = []
#         other_filters[Lifemapper.NAME_KEY] = name
#         other_filters[Lifemapper.ATOM_KEY] = 0
# #         other_filters[Lifemapper.MIN_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
# #         other_filters[Lifemapper.MAX_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
#         if prjscenariocode is not None:
#             other_filters[Lifemapper.SCENARIO_KEY] = prjscenariocode
#         api = LifemapperAPI(
#             resource=Lifemapper.PROJ_RESOURCE, other_filters=other_filters)
#         try:
#             api.query_by_get()
#         except Exception:
#             msg = 'Failed on {}'.format(api.url)
#             log_error(msg, logger=logger)
#             output[S2N.ERRORS_KEY] = msg
#         else:
#             # output returns a list of records
#             recs = api.output
#             if len(recs) == 0:
#                 output['warning'] = 'Failed to find projections for {}'.format(
#                     name)
#             background_layer_name = 'bmng'
#             for rec in recs:
#                 # Add base WMS map url with LM-specific parameters into 
#                 #     map section of metadata
#                 try:
#                     rec['map']['lmMapEndpoint'] = '{}/{}?layers={}'.format(
#                         rec['map']['endpoint'], rec['map']['mapName'],
#                         rec['map']['layerName'])
#                 except Exception as err:
#                     msg = 'Failed getting map url components {}'.format(err)
#                     log_error(msg, logger=logger)
#                     output[S2N.ERRORS_KEY] = msg
#                 else:
#                     # Add background layername into map section of metadata
#                     rec['map']['backgroundLayerName']  = background_layer_name
#                     # Add point layername into map section of metadata
#                     try:
#                         occ_layer_name = 'occ_{}'.format(rec['occurrenceSet']['id'])
#                     except:
#                         occ_layer_name = ''
#                     rec['map']['pointLayerName']  = occ_layer_name
#                     # Add full WMS map url with all required parameters into metadata
#                     url = LifemapperAPI._construct_map_url(
#                         rec, bbox, color, exceptions, height, layers, frmat, 
#                         request, srs, transparent, width)
#                     if url is not None:
#                         rec['map_url'] = url
#         output[S2N.COUNT_KEY] = len(recs)
#         output[S2N.RECORDS_KEY] = recs
#         return output

    # ...............................................
    @classmethod
    def find_map_layers_by_name(
            cls, name, prjscenariocode=None, color=None, other_filters={}, 
            logger=None):
        """
        List projections for a given scientific name.  
        
        Args:
            name: a scientific name 'Accepted' according to the GBIF Backbone 
                Taxonomy
            prjscenariocode: a Lifemapper code indicating whether the 
                environmental data used for creating the projection is 
                observed, or modeled past or future.  Codes are in 
                LmREx.common.lmconstants Lifemapper.*_SCENARIO_CODE*. If the 
                code is None, return a map with only occurrence points
            color: a string indicating a valid color for displaying a predicted
                distribution map 
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Note: 
            Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
            Taxonomy and this method requires them for success.

        Todo:
            handle full record returns instead of atoms
        """
        other_filters[Lifemapper.NAME_KEY] = name
        other_filters[Lifemapper.ATOM_KEY] = 0
#         other_filters[Lifemapper.MIN_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
#         other_filters[Lifemapper.MAX_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
        if prjscenariocode is not None:
            other_filters[Lifemapper.SCENARIO_KEY] = prjscenariocode
        api = LifemapperAPI(
            resource=Lifemapper.PROJ_RESOURCE, other_filters=other_filters)
        qry_meta = {
            S2N.NAME_KEY: name, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        
        try:
            api.query_by_get()
        except Exception as e:
            std_output = {
                S2N.COUNT_KEY: 0, 
                S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
        else:
            std_output = cls._standardize_output(
                api.output, color=color, count_only=False, err=api.error)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
        return std_output

    # ...............................................
    @classmethod
    def find_occurrencesets_by_name(cls, name, logger=None):
        """
        List occurrences for a given scientific name.  
        
        Args:
            name: a scientific name 'Accepted' according to the GBIF Backbone 
                Taxonomy
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Note: 
            Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
            Taxonomy and this method requires them for success.

        Todo:
            handle full record returns instead of atoms
        """
        output = []
        recs = []
        api = LifemapperAPI(
            resource=Lifemapper.OCC_RESOURCE, 
            q_filters={Lifemapper.NAME_KEY: name})
        try:
            api.query_by_get()
        except Exception:
            log_error('Failed on {}'.format(api.url), logger=logger)
        else:
            # Output is list of records?
            recs = api.output
            output[S2N.RECORDS_KEY] = recs
            output[S2N.COUNT_KEY] = len(recs) 
        return output


"""
http://client.lifemapper.org/api/v2/sdmproject?displayname=Conibiosoma%20elongatum&projectionscenariocode=worldclim-curr
http://client.lifemapper.org/api/v2/occurrence?displayname=Conibiosoma%20elongatum
"""
# .............................................................................
class MorphoSourceAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
    PROVIDER = ServiceProvider.MorphoSource['name']
    # ...............................................
    def __init__(
            self, resource=MorphoSource.OCC_RESOURCE, q_filters={}, 
            other_filters={}, logger=None):
        """Constructor for MorphoSourceAPI class"""
        url = '{}/{}/{}'.format(
            MorphoSource.URL, MorphoSource.COMMAND, resource)
        APIQuery.__init__(
            self, url, q_filters=q_filters, 
            other_filters=other_filters, logger=logger)

    # ...............................................
    @classmethod
    def _page_occurrences(cls, start, occid, logger=None):
        output = {'curr_count': 0, S2N.COUNT_KEY: 0, S2N.RECORDS_KEY: []}
        api = MorphoSourceAPI(
            resource=MorphoSource.OCC_RESOURCE, 
            q_filters={MorphoSource.OCCURRENCEID_KEY: occid},
            other_filters={'start': start, 'limit': MorphoSource.LIMIT})
        try:
            api.query_by_get()
        except Exception:
            msg = 'Failed on {}, ({})'.format(api.url, e)
            output[S2N.ERRORS_KEY] = msg
            log_error(msg, logger=logger)
        else:
            # First query, report count
            data = api.output
            output['curr_count'] = data['returnedResults']
            output[S2N.COUNT_KEY] = data['totalResults']
            output[S2N.RECORDS_KEY] = data['results']
        return output

    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def get_occurrences_by_occid_page1(cls, occid, count_only=False, logger=None):
        start = 0
        api = MorphoSourceAPI(
            resource=MorphoSource.OCC_RESOURCE, 
            q_filters={MorphoSource.OCCURRENCEID_KEY: occid},
            other_filters={'start': start, 'limit': MorphoSource.LIMIT})
        qry_meta = {
            S2N.OCCURRENCE_ID_KEY: occid, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [api.url]}
        
        try:
            api.query_by_get()
        except Exception as e:
            std_output = {
                S2N.COUNT_KEY: 0, S2N.ERRORS_KEY: cls._get_error_message(err=e)}
        else:
            std_output = cls._standardize_output(
                api.output, MorphoSource.TOTAL_KEY, MorphoSource.RECORDS_KEY, 
                MorphoSource.RECORD_FORMAT, count_only, err=api.error)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
            # First query, report count
        return std_output


# .............................................................................
class SpecifyPortalAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
    PROVIDER = ServiceProvider.Specify['name']
    # ...............................................
    def __init__(self, url=None, logger=None):
        """Constructor for SpecifyPortalAPI class"""
        if url is None:
            url = 'http://preview.specifycloud.org/export/record'
        APIQuery.__init__(self, url, headers=JSON_HEADERS, logger=logger)


    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_only=False, err=None):
        std_output = {S2N.COUNT_KEY: 0}
        stdrecs = []
        errmsgs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        try:
            recs = [output]
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            std_output[S2N.COUNT_KEY] = len(recs)
        # Records
        if not count_only:
            for r in recs:
                try:
                    stdrecs.append(cls._standardize_record(r))
                except Exception as e:
                    msg = cls._get_error_message(err=e)
                    errmsgs.append(msg)
            # TODO: make sure Specify is using full DWC
            std_output[S2N.RECORD_FORMAT_KEY] = DWC.SCHEMA
            std_output[S2N.RECORDS_KEY] = stdrecs
        std_output[S2N.ERRORS_KEY] = errmsgs
        return std_output

    # ...............................................
    @classmethod
    def get_specify_record(cls, occid, url, count_only, logger=None):
        """Return Specify record published at this url.  
        
        Args:
            url: direct url endpoint for source Specify occurrence record
            
        Note:
            Specify records/datasets without a server endpoint may be cataloged
            in the Solr Specify Resolver but are not resolvable to the host 
            database.  URLs returned for these records begin with 'unknown_url'.
        """
        std_output = {S2N.COUNT_KEY: 0}
        qry_meta = {
            S2N.OCCURRENCE_ID_KEY: occid, S2N.PROVIDER_KEY: cls.PROVIDER,
            S2N.PROVIDER_QUERY_KEY: [url]}
        
        if url.startswith('http'):
            api = APIQuery(url, headers=JSON_HEADERS, logger=logger)
    
            try:
                api.query_by_get()
            except Exception as e:
                std_output = {
                    S2N.COUNT_KEY: 0, 
                    S2N.ERRORS_KEY: [cls._get_error_message(err=e)]}
            else:
                std_output = cls._standardize_output(api.output, count_only)
        # Add query metadata to output
        for key, val in qry_meta.items():
            std_output[key] = val                
        return std_output



# .............................................................................
def test_bison(logger=None):
    """Test Bison
    """
    tsn_list = [['100637', 31], ['100667', 45], ['100674', 24]]

    #       tsn_list = BisonAPI.getTsnListForBinomials()
    for tsn_pair in tsn_list:
        tsn = int(tsn_pair[0])
        count = int(tsn_pair[1])

        new_q = {BISON.HIERARCHY_KEY: '*-{}-*'.format(tsn)}
        occ_api = BisonAPI(
            q_filters=new_q, other_filters=BisonQuery.OCC_FILTERS)
        this_url = occ_api.url
        occ_list = occ_api.get_tsn_occurrences()
        count = None if not occ_list else len(occ_list)
        log_info(
            'Received {} occurrences for TSN {}'.format(count, tsn), 
            logger=logger)

        occ_api2 = BisonAPI.init_from_url(this_url)
        occ_list2 = occ_api2.get_tsn_occurrences()
        count = None if not occ_list2 else len(occ_list2)
        log_info(
            'Received {} occurrences from url init'.format(count),
            logger=logger)

        tsn_api = BisonAPI(
            q_filters={BISON.HIERARCHY_KEY: '*-{}-'.format(tsn)},
            other_filters={'rows': 1})
        hier = tsn_api.get_first_value_for(BISON.HIERARCHY_KEY)
        name = tsn_api.get_first_value_for(BISON.NAME_KEY)
        log_info('{} hierarchy: {}'.format(name, hier), logger=logger)


# .............................................................................
def test_gbif():
    """Test GBIF
    """
    taxon_id = 1000225
    output = GbifAPI.get_taxonomy(taxon_id)
    log_info('GBIF Taxonomy for {} = {}'.format(taxon_id, output))


# .............................................................................
def test_idigbio_taxon_ids():
    """Test iDigBio taxon ids
    """
    in_f_name = '/tank/data/input/idigbio/taxon_ids.txt'
    test_count = 20

    out_list = '/tmp/idigbio_accepted_list.txt'
    if os.path.exists(out_list):
        os.remove(out_list)
    out_f = open(out_list, 'w', encoding=ENCODING)

    idig_list = []
    with open(in_f_name, 'r', encoding=ENCODING) as in_f:
        #          with line in file:
        for _ in range(test_count):
            line = in_f.readline()

            if line is not None:
                temp_vals = line.strip().split()
                if len(temp_vals) < 3:
                    log_error(('Missing data in line {}'.format(line)))
                else:
                    try:
                        curr_gbif_taxon_id = int(temp_vals[0])
                    except Exception:
                        pass
                    try:
                        curr_reported_count = int(temp_vals[1])
                    except Exception:
                        pass
                    temp_vals = temp_vals[1:]
                    temp_vals = temp_vals[1:]
                    curr_name = ' '.join(temp_vals)

                output = GbifAPI.get_taxonomy(curr_gbif_taxon_id)
                tax_status = output[6]

                if tax_status == 'ACCEPTED':
                    idig_list.append(
                        [curr_gbif_taxon_id, curr_reported_count, curr_name])
                    out_f.write(line)

    out_f.close()
    return idig_list

# .............................................................................
if __name__ == '__main__':
    # test
    
    log_info('Mopho records:')
    for guid in TST_VALUES.GUIDS_WO_SPECIFY_ACCESS:
        moutput = MorphoSourceAPI.get_occurrences_by_occid_page1(guid)
        for r in moutput[S2N.RECORDS_KEY]:
            occid = notes = None
            try:
                occid = r['specimen.occurrence_id']
                notes = r['specimen.notes']
            except Exception as e:
                msg = 'Morpho source record exception {}'.format(e)
            else:
                msg = '{}: {}'.format(occid, notes)
            log_info(msg)
    
    namestr = TST_VALUES.NAMES[0]
    clean_names = GbifAPI.parse_names(names=TST_VALUES.NAMES)
    can_name = GbifAPI.parse_name(namestr)
    try:
        acc_name = can_name['canonicalName']
    except Exception as e:
        log_error('Failed to match {}'.format(namestr))
    else:
        acc_names = GbifAPI.match_name(acc_name, status='accepted')
#         log_info('Matched accepted names:')
#         for n in acc_names:
#             log_info('{}: {}, {}'.format(
#                 n['scientificName'], n['status'], n['rank']))
#         log_info ('')
#         syn_names = GbifAPI.match_name(acc_name, status='synonym')
#         log_info('Matched synonyms:')
#         for n in syn_names:
#             log_info('{}: {}, {}'.format(
#                 n['scientificName'], n['status'], n['rank']))
#         log_info ('')
        
#         names = ['ursidae', 'Poa annua']
#         recs = GbifAPI.get_occurrences_by_dataset(TST_VALUES.DATASET_GUIDS[0])
#         log_info('Returned {} records for dataset:'.format(len(recs)))
        names = ['Poa annua']
        for name in names:
            pass
            good_names = GbifAPI.match_name(
                name, match_backbone=True, rank='species')
            log_info('Matched {} with {} GBIF names:'.format(name, len(good_names)))
            for n in good_names:
                log_info('{}: {}, {}'.format(
                    n['scientificName'], n['status'], n['rank']))
            log_info ('')
            itis_names = ItisAPI.match_name(name)
#             log_info ('Matched {} with {} ITIS names using Solr'.format(
#                 name, len(itis_names)))
#             for n in itis_names:
#                 log_info('{}: {}, {}, {}'.format(
#                     n['nameWOInd'], n['kingdom'], n['usage'], n['rank']))
#             log_info ('')
#     
#             itis_names = ItisAPI.match_name(name)
#             log_info ('Matched {} with {} ITIS names using web services'.format(
#                 name, len(itis_names)))
#             for n in itis_names:
#                 log_info('{} {}: {}'.format(
#                     n['tsn'], n['scientificName'], n['nameUsage']))
#             log_info ('')

"""
https://api.gbif.org/v1/occurrence/search?occurrenceId=dbe1622c-1ed3-11e3-bfac-90b11c41863e
url = 'https://search.idigbio.org/v2/search/records/?rq={%22occurrenceid%22%3A%22a413b456-0bff-47da-ab26-f074d9be5219%22}'

"""