import urllib

from LmRex.common.lmconstants import (
    APIService, Itis, ServiceProvider, URL_ESCAPES, TST_VALUES)
from LmRex.fileop.logtools import (log_info, log_error)
from LmRex.services.api.v1.s2n_type import S2nKey, S2nOutput
from LmRex.tools.provider.api import APIQuery

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

# # ...............................................
#     @classmethod
#     def _get_itis_solr_recs(cls, itis_output):
#         std_output = {}
#         errmsgs = []
#         try:
#             data = itis_output['response']
#         except:
#             errmsgs.append(cls._get_error_message(
#                 msg='Missing `response` element'))
#         else:
#             try:
#                 std_output[S2nKey.COUNT] = data['numFound']
#             except:
#                 errmsgs.append(cls._get_error_message(
#                     msg='Missing `count` element'))
#             try:
#                 std_output[S2nKey.RECORDS] = data['docs']
#             except:
#                 errmsgs.append(cls._get_error_message(
#                     msg='Missing `docs` element'))
#         if errmsgs:
#             std_output[S2nKey.ERRORS] = errmsgs
#         return std_output
            
    # ...............................................
    @classmethod
    def _standardize_record(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_key, records_key, record_format, query_term, 
            service, provider_query=[], itis_accepted=False, err=None):
        total = 0
        stdrecs = []
        errmsgs = []
        if err is not None:
            errmsgs.append(err)

        try:
            total = output[count_key]
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
        std_output = S2nOutput(
            total, query_term, service, cls.PROVIDER, 
            provider_query=provider_query, record_format=record_format, 
            records=stdrecs, errors=errmsgs)
        
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

        try:
            api.query()
        except Exception as e:
            std_output = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            try:
                output = api.output['response']
            except:
                if api.error is not None:
                    std_output = cls.get_failure(
                        errors=[cls._get_error_message(err=api.error)])
                else:
                    std_output = cls.get_failure(
                        errors=[cls._get_error_message(
                            msg='Missing `response` element')])
            else:
                # Standardize output from provider response
                std_output = cls._standardize_output(
                    output, Itis.COUNT_KEY, Itis.RECORDS_KEY, Itis.RECORD_FORMAT, 
                    sciname, APIService.Name, provider_query=[api.url], 
                    itis_accepted=itis_accepted, err=api.error)

#         full_out = S2nOutput(
#             count=out.count, record_format=out.record_format, 
#             records=out.records, provider=cls.PROVIDER, errors=out.errors, 
#             provider_query=[api.url], query_term=sciname, 
#             service=APIService.Name)
        return std_output

# ...............................................
    @classmethod
    def get_name_by_tsn(cls, tsn, logger=None):
        """Return a name and kingdom for an ITIS TSN using the ITIS Solr service.
        
        Args:
            tsn: a unique integer identifier for a taxonomic record in ITIS
            
        Note: not used or tested yet
        
        Ex: https://services.itis.gov/?q=tsn:566578&wt=json
        """
        output = {}
        apiq = ItisAPI(
            Itis.SOLR_URL, q_filters={Itis.TSN_KEY: tsn}, logger=logger)
        try:
            apiq.query()
        except Exception as e:
            std_output = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            std_output = cls._standardize_output(
                output, Itis.COUNT_KEY, Itis.RECORDS_KEY, Itis.RECORD_FORMAT, 
                tsn, APIService.Name, provider_query=[apiq.url], 
                itis_accepted=True, err=apiq.error)

        return std_output


    # ...............................................
    def query(self):
        """Queries the API and sets 'output' attribute to a JSON object"""
        APIQuery.query_by_get(self, output_type='json')

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
# 
#     # ...............................................
#     @classmethod
#     def get_tsn_hierarchy(cls, tsn, logger=None):
#         """Retrieve taxon hierarchy"""
#         url = '{}/{}'.format(Itis.WEBSVC_URL, Itis.TAXONOMY_HIERARCHY_QUERY)
#         apiq = APIQuery(
#             url, other_filters={Itis.TSN_KEY: tsn}, 
#             headers={'Content-Type': 'text/xml'}, logger=logger)
#         apiq.query_by_get(output_type='xml')
#         tax_path = apiq._return_hierarchy()
#         hierarchy = {}
#         for rank in (
#                 Itis.KINGDOM_KEY, Itis.PHYLUM_DIVISION_KEY, Itis.CLASS_KEY,
#                 Itis.ORDER_KEY, Itis.FAMILY_KEY, Itis.GENUS_KEY,
#                 Itis.SPECIES_KEY):
#             hierarchy[rank] = apiq._get_rank_from_path(tax_path, rank)
#         return hierarchy

# # ...............................................
#     @classmethod
#     def match_name_nonsolr(cls, sciname, count_only=False, outformat='json', logger=None):
#         """Return matching names for scienfific name using the ITIS Web service.
#         
#         Args:
#             sciname: a scientific name
#             
#         Ex: https://services.itis.gov/?q=tsn:566578&wt=json
#         """
#         output = {}
#         errmsgs = []
#         if outformat == 'json':
#             url = Itis.JSONSVC_URL
#         else:
#             url = Itis.WEBSVC_URL
#             outformat = 'xml'
#         apiq = ItisAPI(
#             url, service=Itis.ITISTERMS_FROM_SCINAME_QUERY, 
#             other_filters={Itis.SEARCH_KEY: sciname}, logger=logger)
#         apiq.query_by_get(output_type=outformat)
#         
#         recs = []
#         if outformat == 'json':    
#             outjson = apiq.output
#             try:
#                 recs = outjson['itisTerms']
#             except:
#                 errmsgs.append(cls._get_error_message(
#                     msg='Missing `itisTerms` element'))
#         else:
#             root = apiq.output    
#             retElt = root.find('{}return'.format(Itis.NAMESPACE))
#             if retElt is not None:
#                 termEltLst = retElt.findall('{}itisTerms'.format(Itis.DATA_NAMESPACE))
#                 for tElt in termEltLst:
#                     rec = {}
#                     elts = tElt.getchildren()
#                     for e in elts:
#                         rec[e.tag] = e.text
#                     if rec:
#                         recs.append(rec)
#                         
#         output[S2nKey.COUNT] = len(recs)
#         if not count_only:
#             output[S2nKey.RECORDS] = recs
#             output[S2nKey.RECORD_FORMAT] = 'tbd'
#         output[S2nKey.ERRORS] = errmsgs
#         return output

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.tools.provider.gbif import GbifAPI
    
    names = TST_VALUES.NAMES[:5]
    canonicals = GbifAPI.parse_names(names=names)
    
    for name in names:
        itis_names = ItisAPI.match_name(name)
        log_info ('Matched {} with {} ITIS names using Solr'.format(
            name, len(itis_names)))
        for n in itis_names:
            log_info('{}: {}, {}, {}'.format(
                n['nameWOInd'], n['kingdom'], n['usage'], n['rank']))
        log_info ('')
 
