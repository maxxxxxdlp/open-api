"""Module containing functions for API Queries"""
from copy import copy
import csv
import os
import requests
import urllib
import xml.etree.ElementTree as ET

# import idigbio
from LmRex.common.lmconstants import (
    BISON, BisonQuery, GBIF, HTTPStatus, Idigbio, Itis, MorphoSource, 
    URL_ESCAPES, ENCODING, JSON_HEADERS, TST_VALUES)
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
        self.debug = False

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
        """Retrieve a url for the query
        """
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
    @staticmethod
    def _interpret_q_clause(key, val, logger=None):
        cls = None
        if isinstance(val, (float, int, str)):
            cls = '{}:{}'.format(key, str(val))
        # Tuple for negated or range value
        elif isinstance(val, tuple):
            # negated filter
            if isinstance(val[0], bool) and val[0] is False:
                cls = 'NOT ' + key + ':' + str(val[1])
            # range filter (better be numbers)
            elif isinstance(
                    val[0], (float, int)) and isinstance(val[1], (float, int)):
                cls = '{}:[{} TO {}]'.format(key, str(val[0]), str(val[1]))
            else:
                log_warn('Unexpected value type {}'.format(val), logger=logger)
        else:
            log_warn('Unexpected value type {}'.format(val), logger=logger)
        return cls

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
        """Queries the API and sets 'output' attribute to a JSON or 
        ElementTree object.
        """
        self.output = None
        ret_code = None
        try:
            response = requests.get(self.url, headers=self.headers)
        except Exception as e:
            log_error(
                'Failed on URL {}, ({})'.format(self.url, str(e)), 
                logger=self.logger)
        else:
            if response.status_code == HTTPStatus.OK:
                if output_type == 'json':
                    try:
                        self.output = response.json()
                    except Exception as e:
                        output = response.content
                        self.output = deserialize(fromstring(output))
                elif output_type == 'xml':
                    try:
                        output = fromstring(response.text)
                        self.output = output
                    except Exception as e:
                        self.output = response.text
                else:
                    log_error(
                        'Unrecognized output type {}'.format(output_type), 
                        logger=self.logger)
            else:
                log_error(
                    'Failed on URL {}, code = {}, reason = {}'.format(
                        self.url, response.status_code, response.reason), 
                    logger=self.logger)

    # ...........    ....................................
    def query_by_post(self, output_type='json', file=None):
        """Perform a POST request."""
        self.output = None
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
                log_error(
                    """Failed on URL {}, posting uploaded file {}, code = {},
                        reason = {} ({})""".format(
                            self.url, file, ret_code, reason, str(e)), 
                        logger=self.logger)
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
                log_error(
                    'Failed on URL {}, code = {}, reason = {} ({})'.format(
                        self.url, ret_code, reason, str(e)), 
                    logger=self.logger)

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
                    log_error(
                        'Unrecognized output type {}'.format(output_type),
                        logger=self.logger)
            except Exception as e:
                log_error(
                    'Failed to interpret output of URL {}, content={}, ({})'
                    .format(self.base_url, response.content, str(e)),
                    logger=self.logger)
        else:
            try:
                ret_code = response.status_code
                reason = response.reason
            except Exception:
                ret_code = HTTPStatus.INTERNAL_SERVER_ERROR
                reason = 'Unknown Error'
            log_error(
                'Failed ({}: {}) for baseurl {}'.format(
                    ret_code, reason, self.base_url), 
                logger=self.logger)


# .............................................................................
class BisonAPI(APIQuery):
    """Class to query BISON APIs and return results
    """

    # ...............................................
    def __init__(self, q_filters=None, other_filters=None, filter_string=None,
                 headers=None, logger=None):
        """Constructor for BisonAPI class
        """
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        all_q_filters = copy(BisonQuery.QFILTERS)
        if q_filters:
            all_q_filters.update(q_filters)

        # Add/replace other filters to defaults for this instance
        all_other_filters = copy(BisonQuery.FILTERS)
        if other_filters:
            all_other_filters.update(other_filters)

        APIQuery.__init__(
            self, BISON.OCCURRENCE_URL, q_key='q', q_filters=all_q_filters,
            other_filters=all_other_filters, filter_string=filter_string,
            headers=headers, logger=logger)

    # ...............................................
    @classmethod
    def init_from_url(cls, url, headers=None, logger=None):
        """Instiate from url
        """
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        base, filters = url.split('?')
        if base.strip().startswith(BISON.OCCURRENCE_URL):
            qry = BisonAPI(filter_string=filters, logger=logger)
        else:
            raise Exception(
                'Bison occurrence API must start with {}'.format(
                    BISON.OCCURRENCE_URL))
        return qry

    # ...............................................
    def query(self):
        """Queries the API and sets 'output' attribute to a JSON object
        """
        APIQuery.query_by_get(self, output_type='json')

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
    @staticmethod
    def get_tsn_list_for_binomials(logger=None):
        """Returns a list of sequences containing tsn and tsnCount
        """
        bison_qry = BisonAPI(
            q_filters={BISON.NAME_KEY: BISON.BINOMIAL_REGEX},
            other_filters=BisonQuery.TSN_FILTERS, logger=logger)
        tsn_list = bison_qry._get_binomial_tsns()
        return tsn_list

    # ...............................................
    def _get_binomial_tsns(self):
        data_list = None
        self.query()
        if self.output is not None:
            data_count = self._burrow(BisonQuery.COUNT_KEYS)
            data_list = self._burrow(BisonQuery.TSN_LIST_KEYS)
            log_info(
                'Reported count = {}, actual count = {}'.format(
                    data_count, len(data_list)), 
                logger=self.logger)
        return data_list

    # ...............................................
    @staticmethod
    def get_itis_tsn_values(itis_tsn, logger=None):
        """Return ItisScientificName, kingdom, and TSN info for occ record
        """
        itis_name = king = tsn_hier = None
        try:
            occ_api = BisonAPI(
                q_filters={BISON.HIERARCHY_KEY: '*-{}-'.format(itis_tsn)},
                other_filters={'rows': 1}, logger=logger)
            tsn_hier = occ_api.get_first_value_for(BISON.HIERARCHY_KEY)
            itis_name = occ_api.get_first_value_for(BISON.NAME_KEY)
            king = occ_api.get_first_value_for(BISON.KINGDOM_KEY)
        except Exception as e:
            log_error(str(e))
            raise
        return (itis_name, king, tsn_hier)

    # ...............................................
    def get_tsn_occurrences(self):
        """Returns a list of occurrence record dictionaries
        """
        data_list = []
        if self.output is None:
            self.query()
        if self.output is not None:
            data_list = self._burrow(BisonQuery.RECORD_KEYS)
        return data_list

    # ...............................................
    def get_first_value_for(self, field_name):
        """Returns first value for given field name
        """
        val = None
        records = self.get_tsn_occurrences()
        for rec in records:
            try:
                val = rec[field_name]
                break
            except KeyError:
                log_error(
                    'Missing {} for {}'.format(field_name, self.url), 
                    logger=self.logger)
        return val


# .............................................................................
class ItisAPI(APIQuery):
    """Class to pull data from the ITIS Solr or Web service, documentation at:
        https://www.itis.gov/solr_documentation.html and 
        https://www.itis.gov/web_service.html
    """

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
    @staticmethod
    def _get_fld_value(doc, fldname):
        try:
            val = doc[fldname]
        except:
            val = None
        return val

    # ...............................................
    @staticmethod
    def _get_rank_from_path(tax_path, rank_key):
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
    @staticmethod
    def _get_itis_solr_recs(output):
        try:
            data = output['response']
        except:
            raise Exception('Failed to return response element')
        try:
            docs = data['docs']
        except:
            raise Exception('Failed to return docs')
        return docs
    
# ...............................................
    @staticmethod
    def _get_itis_json_recs(output):
        try:
            data = output['response']
        except:
            raise Exception('Failed to return response element')
        try:
            docs = data['docs']
        except:
            raise Exception('Failed to return docs')
        return docs
    
# ...............................................
    @staticmethod
    def map_record(rec, mapping):
        """
        Map old record to new, pulling values from returned record which may be 
        nested several levels.
        
        Args:
            rec: json/dictionary returned from a web service
            mapping: dictionary mapping new records to returned records with 
                keys = new fieldnames and values = a sequence of filed
        """
        newrec = {}
        for new_fld, orig_fields in mapping.items():
            val = rec
            for ofld in orig_fields:
                val = val[ofld]
            newrec[new_fld] = val
            
            
# ...............................................
    @staticmethod
    def match_name_solr(sciname, status=None, kingdom=None, logger=None):
        """Return an ITIS record for a scientific name using the 
        ITIS Solr service.
        
        Args:
            sciname: a scientific name designating a taxon
            status: optional designation for taxon status, 
                kingdom Plantae are valid/invalid, others are accepted 
            kingdom: optional designation for kingdom 
            
        Ex: http://services.itis.gov/?q=nameWOInd:Spinus\%20tristis&wt=json
        """
        matches = []
        q_filters = {Itis.NAME_KEY: sciname}
        if kingdom is not None:
            q_filters['kingdom'] = kingdom
        apiq = ItisAPI(Itis.SOLR_URL, q_filters=q_filters, logger=logger)
        apiq.query()
#         apiq.query_by_get()
        docs = apiq._get_itis_solr_recs(apiq.output)

        for doc in docs:
            if status is None:
                matches.append(doc)
            else:
                usage = doc['usage'].lower()
                if (status in ('accepted', 'valid') and 
                    usage in ('accepted', 'valid')):
                    matches.append(doc)
                elif status == usage:
                    matches.append(doc)
#             else:
#                 accepted_tsn_list = apiq._get_fld_value(doc, 'acceptedTSN')
#                 for tsn in accepted_tsn_list:
#                     acc_recs = ItisAPI.get_name(tsn)
#                     matches.extend(acc_recs)
        log_info('ITIS Solr returned {} matches for sciname {}'.format(
            len(matches), sciname), logger=logger)
        return matches
    
# ...............................................
    @staticmethod
    def match_name(sciname, outformat='json', logger=None):
        """Return matching names for scienfific name using the ITIS Web service.
        
        Args:
            sciname: a scientific name
            
        Ex: https://services.itis.gov/?q=tsn:566578&wt=json
        """
        recs = []
        if outformat == 'json':
            url = Itis.JSONSVC_URL
        else:
            url = Itis.WEBSVC_URL
            outformat = 'xml'
        apiq = ItisAPI(
            url, service=Itis.ITISTERMS_FROM_SCINAME_QUERY, 
            other_filters={Itis.SEARCH_KEY: sciname}, logger=logger)
        apiq.query_by_get(output_type=outformat)
        
        if outformat == 'json':    
#             recs = apiq._get_itis_json_recs(apiq.output)
            outjson = apiq.output
            try:
                recs = outjson['itisTerms']
            except:
                log_error(
                    'itisTerms is not present in output, keys = {}'.format(
                        outjson.keys()), logger=logger)
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
        log_info('ITIS WS returned {} matches for sciname {}'.format(
            len(recs), sciname), logger=logger)
        return recs

# ...............................................
    @staticmethod
    def get_name_by_tsn_solr(tsn, logger=None):
        """Return a name and kingdom for an ITIS TSN using the ITIS Solr service.
        
        Args:
            tsn: a unique integer identifier for a taxonomic record in ITIS
            
        Ex: https://services.itis.gov/?q=tsn:566578&wt=json
        """
        apiq = ItisAPI(
            Itis.SOLR_URL, q_filters={Itis.TSN_KEY: tsn}, logger=logger)
        docs = apiq.get_itis_recs()
        recs = []
        for doc in docs:
            usage = doc['usage']
            if usage in ('accepted', 'valid'):
                recs.append(doc)
        return recs

# # ...............................................
#     @staticmethod
#     def get_vernacular_by_tsn(tsn, logger=None):
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
    @staticmethod
    def get_tsn_hierarchy(tsn, logger=None):
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
    # ...............................................
    def __init__(self, service=GBIF.SPECIES_SERVICE, key=None,
                 other_filters=None, logger=None):
        """Constructor for GbifAPI class
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
    @staticmethod
    def _get_output_val(out_dict, name):
        try:
            tmp = out_dict[name]
            val = str(tmp).encode(ENCODING)
        except Exception:
            return None
        return val

    # ...............................................
    @staticmethod
    def get_taxonomy(taxon_key, logger=None):
        """Return GBIF backbone taxonomy for this GBIF Taxon ID
        """
        accepted_key = accepted_str = nub_key = None
        tax_api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key=taxon_key, logger=logger)

        try:
            tax_api.query()
            sciname_str = tax_api._get_output_val(
                tax_api.output, 'scientificName')
            kingdom_str = tax_api._get_output_val(tax_api.output, 'kingdom')
            phylum_str = tax_api._get_output_val(tax_api.output, 'phylum')
            class_str = tax_api._get_output_val(tax_api.output, 'class')
            order_str = tax_api._get_output_val(tax_api.output, 'order')
            family_str = tax_api._get_output_val(tax_api.output, 'family')
            genus_str = tax_api._get_output_val(tax_api.output, 'genus')
            species_str = tax_api._get_output_val(tax_api.output, 'species')
            rank_str = tax_api._get_output_val(tax_api.output, 'rank')
            genus_key = tax_api._get_output_val(tax_api.output, 'genusKey')
            species_key = tax_api._get_output_val(tax_api.output, 'speciesKey')
            tax_status = tax_api._get_output_val(
                tax_api.output, 'taxonomicStatus')
            canonical_str = tax_api._get_output_val(
                tax_api.output, 'canonicalName')
            if tax_status != 'ACCEPTED':
                try:
                    # Not present if results are taxonomicStatus=ACCEPTED
                    accepted_key = tax_api._get_output_val(
                        tax_api.output, 'acceptedKey')
                    accepted_str = tax_api._get_output_val(
                        tax_api.output, 'accepted')
                    nub_key = tax_api._get_output_val(tax_api.output, 'nubKey')

                except Exception:
                    log_warn(
                        'Failed to format data from {}'.format(taxon_key), 
                        logger)
        except Exception as e:
            log_error(str(e), logger=logger)
            raise
        return (
            rank_str, sciname_str, canonical_str, accepted_key, accepted_str,
            nub_key, tax_status, kingdom_str, phylum_str, class_str, order_str,
            family_str, genus_str, species_str, genus_key, species_key)

    # ...............................................
    @staticmethod
    def _get_taiwan_row(occ_api, taxon_key, canonical_name, rec):
        row = None
        occ_key = occ_api._get_output_val(rec, 'gbifID')
        lon_str = occ_api._get_output_val(rec, 'decimalLongitude')
        lat_str = occ_api._get_output_val(rec, 'decimalLatitude')
        try:
            float(lon_str)
        except ValueError:
            return row

        try:
            float(lat_str)
        except ValueError:
            return row

        if (occ_key is not None
                and not lat_str.startswith('0.0')
                and not lon_str.startswith('0.0')):
            row = [taxon_key, canonical_name, occ_key, lon_str, lat_str]
        return row

    # ...............................................
    @staticmethod
    def get_occurrences(taxon_key, canonical_name, out_f_name,
                        other_filters=None, max_points=None, logger=None):
        """Return GBIF occurrences for this GBIF Taxon ID
        """
        gbif_api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={
                'taxonKey': taxon_key, 'limit': GBIF.LIMIT,
                'hasCoordinate': True, 'has_geospatial_issue': False},
            logger=logger)

        gbif_api.add_filters(q_filters=other_filters)

        offset = 0
        curr_count = 0
        lm_total = 0
        gbif_total = 0
        complete = False

        ready_filename(out_f_name, overwrite=True)
        with open(out_f_name, 'w', encoding=ENCODING, newline='') as csv_f:
            writer = csv.writer(csv_f, delimiter=GbifAPI.DELIMITER)

            while not complete and offset <= gbif_total:
                gbif_api.add_filters(other_filters={'offset': offset})
                try:
                    gbif_api.query()
                except Exception:
                    log_error('Failed on {}'.format(taxon_key), logger=logger)
                    curr_count = 0
                else:
                    # First query, report count
                    if offset == 0:
                        gbif_total = gbif_api.output['count']
                        log_info('GBIF reports {} recs for key {}'.format(
                            gbif_total, taxon_key), logger=logger)

                    recs = gbif_api.output['results']
                    curr_count = len(recs)
                    lm_total += curr_count
                    # Write header
                    if offset == 0 and curr_count > 0:
                        writer.writerow(
                            ['taxonKey', 'canonicalName', 'gbifID',
                             'decimalLongitude', 'decimalLatitude'])
                    # Write recs
                    for rec in recs:
                        row = gbif_api._get_taiwan_row(
                            gbif_api, taxon_key, canonical_name, rec)
                        if row:
                            writer.writerow(row)
                    log_info(
                        '  Retrieved {} records, starting at {}'.format(
                            curr_count, offset), logger=logger)
                    offset += GBIF.LIMIT
                    if max_points is not None and lm_total >= max_points:
                        complete = True

    # ...............................................
    @staticmethod
    def get_specimen_records_by_occid(occid, logger=None):
        """Return GBIF occurrences for this occurrenceId.  This should retrieve 
        a single record if the occurrenceId is unique.
        """
        recs = []
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={'occurrenceID': occid}, logger=logger)

        try:
            api.query()
        except Exception:
            log_error('Failed on {}'.format(occid), logger=logger)
        else:
            # First query, report count
            total = api.output['count']
            log_info(
                'GBIF returned {} recs for occurrenceId {}'.format(total, occid), 
                logger=logger)
            recs = api.output['results']
        return recs

    # ...............................................
    @staticmethod
    def _get_fld_vals(big_rec):
        rec = {}
        for fld_name in GbifAPI.NameMatchFieldnames:
            try:
                rec[fld_name] = big_rec[fld_name]
            except KeyError:
                pass
        return rec

    # ...............................................
    @staticmethod
    def get_records_by_dataset(dataset_key, logger=None):
        all_recs = []
        offset = 0
        is_end = False        
        while not is_end:
            api = GbifAPI(
                service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
                other_filters={
                    'dataset_key': dataset_key, 'offset': offset, 
                    'limit': GBIF.LIMIT}, logger=logger)
            try:
                api.query()
            except Exception:
                log_error('Failed on {}'.format(dataset_key), logger=logger)
            else:
                total = api.output['count']
                is_end = bool(api.output['endOfRecords'])
                recs = api.output['results']
                if recs:
                    all_recs.extend(recs)
                    offset += len(recs)
                    log_info(
                        'Returned {} of {} GBIF recs for dataset {}'.format(
                            len(recs), total, dataset_key), logger=logger)
                # TODO: handle large queries another way
                # Throttle during testing
                if offset >= (GBIF.LIMIT * 2):
                    is_end = True
        return all_recs


    # ...............................................
    @staticmethod
    def match_name(name_str, status=None, logger=None):
        """Return closest accepted species in GBIF backbone taxonomy,
        
        Args:
            name_str: A scientific namestring possibly including author, year, 
                rank marker or other name information.
            kingdom: optional kingdom of the desired results, helps to 
                narrow down results in the event of duplicate names in different
                kingdoms.
                
        Returns:
            Either a dictionary containing a matching record with status 
                'accepted' or 'synonym' without 'alternatives'.  
            Or, if there is no matching record, return the first/best 
                'alternative' record with status 'accepted' or 'synonym'.

        Note:
            This function uses the name search API, 
        """
        matches = []
        name_clean = name_str.strip()

        other_filters = {'name': name_clean, 'verbose': 'true'}
#         if rank:
#             other_filters['rank'] = rank
#         if kingdom:
#             other_filters['kingdom'] = kingdom
        name_api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key='match',
            other_filters=other_filters, logger=logger)
        try:
            name_api.query()
            output = name_api.output
        except Exception as e:
            log_error(
                'Failed to get a response for species match on {}, ({})'.format(
                    name_clean, str(e)), logger=logger)
            raise

        # Pull alternatives out of record
        try:
            alternatives = output.pop('alternatives')
        except Exception as e:
            alternatives = []
            
        is_match = True
        try:
            if output['matchType'].lower() == 'none':
                is_match = False
        except AttributeError:
            log_error(
                'No matchType for record matching {}'.format(name_clean), 
                logger=logger)
        else:
            # No filter by status
            if is_match:
                if status is None:
                    matches.append(output)
                    for alt in alternatives:
                        matches.append(alt)
                # Check status of upper level result
                else:
                    outstatus = None
                    try:
                        outstatus = output['status'].lower()
                    except AttributeError:
                        log_error(
                            'No status for record matching {}'.format(
                                name_clean), logger=logger)
                    else:
                        if outstatus == status:
                            matches.append(output)
                    # Check status of alternative results result            
                    for alt in alternatives:
                        outstatus = None
                        try:
                            outstatus = alt['status'].lower()
                        except AttributeError:
                            log_error(
                                'No status for alternative matching {}'.format(
                                    name_clean), logger=logger)
                        else:
                            if outstatus == status:
                                matches.append(alt)
        log_info('GBIF returned {} matches for name {}'.format(
            len(matches), name_clean), logger=logger)
        return matches

    # ......................................
    @staticmethod
    def _post_json_to_parser(url, data, logger=None):
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
    @staticmethod
    def _trim_parsed_output(output, logger=None):
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
    @staticmethod
    def parse_name(namestr, logger=None):
        """
        Send a scientific name to the GBIF Parser returning a canonical name.
        
        Args:
            namestr: A scientific namestring possibly including author, year, 
                rank marker or other name information.
                
        Returns:
            A record as a dictionary containing a parsed scientific name, with 
            keys being the part of a scientific name, and values being the 
            element or elements that correspond to that part.
            
        sent (bad) http://api.gbif.org/v1/parser/name?name=Acer%5C%2520caesium%5C%2520Wall.%5C%2520ex%5C%2520Brandis
        send good http://api.gbif.org/v1/parser/name?name=Acer%20heldreichii%20Orph.%20ex%20Boiss.
        """
        rec = None
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
                rec = recs[0]
            except:
                pass
#             log_info('GBIF returned {} parsed records for {}'.format(
#                 len(recs), namestr), logger=logger)
        return rec

    # ...............................................
    @staticmethod
    def parse_names(names=[], filename=None, logger=None):
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
                    'GBIF returned {} parsed records for file {}'.format(
                        len(recs), filename), logger=logger)
            else:
                log_info(
                    'GBIF returned {} parsed records for {} names'.format(
                        len(recs), len(names)), logger=logger)

        return recs

    # ...............................................
    @staticmethod
    def get_publishing_org(pub_org_key, logger=None):
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
    """Class to query iDigBio APIs and return results
    """
    OCCURRENCE_COUNT_KEY = 'count'

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
    def query_by_gbif_taxon_id(self, taxon_key):
        """Return a list of occurrence record dictionaries.
        """
        self._q_filters[Idigbio.GBIFID_FIELD] = taxon_key
        self.query()
        specimen_list = []
        if self.output is not None:
            # full_count = self.output['itemCount']
            for item in self.output[Idigbio.OCCURRENCE_ITEMS_KEY]:
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
    @staticmethod
    def get_records_by_occid(occid, logger=None):
        """Return iDigBio occurrences for this occurrenceId.  This will
        retrieve a one or more records with the given occurrenceId.
        """
        recs = []
        qf = {Idigbio.QKEY: 
              '{"' + Idigbio.OCCURRENCEID_FIELD + '":"' + occid + '"}'}
        api = IdigbioAPI(other_filters=qf, logger=logger)

        try:
            api.query()
        except Exception:
            log_error('Failed on {}'.format(occid), logger=logger)
        else:
            recs = []
            if api.output is not None:
                total = api.output['itemCount']
                log_info(
                    'iDigBio returned {} recs for Specify occurrenceId {}'.format(
                        total, occid), logger=logger)
                recs = api.output[Idigbio.OCCURRENCE_ITEMS_KEY]
        return recs

    # ...............................................
    @staticmethod
    def _write_idigbio_metadata(orig_fld_names, meta_f_name):
        pass

    # ...............................................
    @staticmethod
    def _get_idigbio_fields(rec):
        """Get iDigBio fields
        """
        fld_names = list(rec['indexTerms'].keys())
        # add dec_long and dec_lat to records
        fld_names.extend(['dec_lat', 'dec_long'])
        fld_names.sort()
        return fld_names

#     # ...............................................
#     @staticmethod
#     def _count_idigbio_records(gbif_taxon_id):
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
class MorphoSourceAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
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
    @staticmethod
    def _page_specimen_records(start, occid, logger=None):
        recs = []
        total = curr_total = 0
        api = MorphoSourceAPI(
            resource=MorphoSource.OCC_RESOURCE, 
            q_filters={MorphoSource.OCCURRENCEID_KEY: occid},
            other_filters={'start': start, 'limit': MorphoSource.LIMIT})
        try:
            api.query_by_get()
        except Exception:
            log_error('Failed on {}'.format(occid), logger=logger)
        else:
            # First query, report count
            data = api.output
            curr_total = data['returnedResults']
            total = data['totalResults']
            recs = data['results']
        return recs, curr_total, total

    # ...............................................
    @staticmethod
    def get_specimen_records_by_occid(occid, logger=None):
        start = 0
        recs, curr_total, total = MorphoSourceAPI._page_specimen_records(
            start, occid, logger=logger)
        if curr_total < total:
            start = MorphoSource.LIMIT
            loops = int(total/MorphoSource.LIMIT)
            for i in loops:
                curr_recs, curr_total, total = MorphoSourceAPI._page_specimen_records(
                    start, occid, logger=logger)
                if curr_recs:
                    recs.extend(curr_recs)
        log_info(
            'Returned {} of {} MorphoSource recs for occurrence {}'.format(
                len(recs), total, occid), logger=logger)
        return recs

# .............................................................................
class SpecifyPortalAPI(APIQuery):
    """Class to query Specify portal APIs and return results"""
    # ...............................................
    def __init__(self, url=None, logger=None):
        """Constructor for SpecifyPortalAPI class"""
        if url is None:
            url = 'http://preview.specifycloud.org/export/record'
        APIQuery.__init__(self, url, headers=JSON_HEADERS, logger=logger)

    # ...............................................
    @staticmethod
    def get_specify_record(url, logger=None):
        """Return Specify record published at this url.  
        
        Args:
            url: direct url endpoint for source Specify occurrence record
            
        Note:
            Specify records/datasets without a server endpoint may be cataloged
            in the Solr Specify Resolver but are not resolvable to the host 
            database.  URLs returned for these records begin with 'unknown_url'.
        """
        rec = {}
        if url.startswith('http'):
            api = APIQuery(url, headers=JSON_HEADERS, logger=logger)
    
            try:
                api.query_by_get()
            except Exception:
                log_error('Failed on {}'.format(url), logger=logger)
            else:
                rec = api.output
        return rec



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
    for guid in TST_VALUES.BIRD_OCC_GUIDS:
        recs = MorphoSourceAPI.get_specimen_records_by_occid(guid)
        for r in recs:
            try:
                notes = r['specimen.notes']
            except:
                notes = 'no notes'
            log_info('{}: {}'.format(
                r['specimen.occurrence_id'], notes))
        log_info ('')
    
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
#         recs = GbifAPI.get_records_by_dataset(TST_VALUES.DATASET_GUIDS[0])
#         log_info('Returned {} records for dataset:'.format(len(recs)))
#         names = ['Poa annua']
#         for name in names:
#             pass
#             good_names = GbifAPI.match_name(
#                 name, match_backbone=True, rank='species')
#             log_info('Matched {} with {} GBIF names:'.format(name, len(good_names)))
#             for n in good_names:
#                 log_info('{}: {}, {}'.format(
#                     n['scientificName'], n['status'], n['rank']))
#             log_info ('')
#             itis_names = ItisAPI.match_name_solr(name)
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