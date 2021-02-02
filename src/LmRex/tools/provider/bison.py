from copy import copy

from LmRex.common.lmconstants import (
    BISON, BisonQuery, ServiceProvider, TST_VALUES)
from LmRex.fileop.logtools import (log_info)

from LmRex.services.api.v1.s2n_type import S2nKey
from LmRex.tools.provider.api import APIQuery

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
            S2nKey.COUNT: limit}

        api = BisonAPI(
            url=BISON.OPEN_SEARCH_URL, other_filters=ofilters, logger=logger)
        qry_meta = {
            S2nKey.NAME: namestr, S2nKey.PROVIDER: cls.PROVIDER, 
            S2nKey.PROVIDER_QUERY: [api.url]}

        try:
            api.query_by_get()
        except Exception as e:
            std_output = {S2nKey.ERRORS: [cls._get_error_message(err=e)]}
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
