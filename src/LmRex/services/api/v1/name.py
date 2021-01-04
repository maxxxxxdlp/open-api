import cherrypy

from LmRex.common.lmconstants import TST_VALUES
from LmRex.services.api.v1.base import S2nService
from LmRex.tools.api import (GbifAPI, ItisAPI)



# .............................................................................
@cherrypy.expose
class _NameSvc(S2nService):
    
    @cherrypy.tools.json_out()
    def _show_online(self, msg):
        return {'info': msg}

#     # ...............................................
#     def parse_name_with_gbif(self, namestr):
#         output = GbifAPI.parse_name(namestr)
#         try:
#             namestr = output['record']['canonicalName']
#         except:
#             # Default to original namestring if parsing fails
#             pass
#         return namestr
# 
#     # ...............................................
#     def match_name_with_itis(self, namestr):
#         output = ItisAPI.match_name_solr(namestr, status='valid')
#         try:
#             namestr = output['records'][0]['nameWOInd']
#         except:
#             # Default to original namestring if match fails
#             pass
#         return namestr

#     # ...............................................
#     @cherrypy.tools.json_out()
#     def _standardize_params(
#             self, namestr=None, gbif_accepted=True, gbif_parse=True, 
#             gbif_count=True, status=None, kingdom=None):
#         """
#         Standardize the parameters for all Name Services into a dictionary with 
#         all keys as standardized parameter names and values as correctly-typed 
#         user values or defaults. 
#         
#         Args:
#             namestr: a scientific name
#             gbif_accepted: flag to indicate whether to limit to "Accepted" 
#                 taxa in the GBIF Backbone Taxonomy
#             gbif_parse: flag to indicate whether to first use the GBIF parser 
#                 to parse a scientific name into canonical name
#             gbif_count: flag to indicate whether to count occurrences in 
#                 service provider for this taxon
#             status: filter for ITIS records with this status
#             kingdom: filter for ITIS records from this kingdom
#         Return:
#             a dictionary containing keys and properly formated values for the
#                 user specified parameters.
#         """
#         kwarg_defaults = {
#             'namestr': (None, ''), 
#             'gbif_accepted': False, 'gbif_parse': False, 'gbif_count': False, 
#             'status': (None, ''), 'kingdom': (None, '')}
#         user_kwargs = {
#             'namestr': namestr, 'gbif_accepted': gbif_accepted, 
#             'gbif_parse': gbif_parse, 'gbif_count': gbif_count, 'status': status, 
#             'kingdom': kingdom}
#         usr_params = self._process_params(kwarg_defaults, user_kwargs)
#         # Remove 'gbif_accepted' flag and replace with 'gbif_status' filter for GBIF
#         gbif_accepted = usr_params.pop('gbif_accepted')
#         if gbif_accepted is True:
#             usr_params['gbif_status'] = 'accepted'
#         else:
#             usr_params['gbif_status'] = None
#         # Remove 'gbif_parse' flag
#         gbif_parse = usr_params.pop('gbif_parse')
#         namestr = usr_params['namestr']
#         # Replace namestr with GBIF-parsed namestr
#         if namestr and gbif_parse: 
#             usr_params['namestr'] = self.parse_name_with_gbif(namestr)
#         return usr_params

# .............................................................................
@cherrypy.expose
class GAcName(_NameSvc):
    # ...............................................
    def get_gbif_matching_taxon(self, namestr, gbif_status, gbif_count):
        output = {}
        # Get name from Gbif        
        moutput = GbifAPI.match_name(namestr, status=gbif_status)        
        good_names = moutput['records']
        output['count'] = moutput['count']
        if gbif_count is True:
            for namerec in good_names:
                try:
                    taxon_key = namerec['usageKey']
                except Exception as e:
                    print('Exception on {}: {}'.format(namestr, e))
                    print('name = {}'.format(namerec))
                else:
                    # Add more info to each record
                    output2 = GbifAPI.count_occurrences_for_taxon(taxon_key)
                    namerec['occurrence_count'] = output2['count']
                    namerec['occurrences_url'] = output2['url']
        output['records'] = good_names
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, **kwargs):
        """Get GBIF taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_accepted: flag to indicate whether to filter by 
                status='accepted' 
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            gbif_count: flag to indicate whether to count GBIF occurrences of 
                this taxon
            kwargs: additional keyword arguments - to be ignored
        Return:
            a dictionary containing a count and list of dictionaries of 
                GBIF records corresponding to names in the GBIF backbone 
                taxonomy
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
            gbif_count=gbif_count)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online('S^n Name resolution is online')
        else:
            return self.get_gbif_matching_taxon(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'])

# .............................................................................
@cherrypy.expose
class ITISName(_NameSvc):
    """
    Note:
        Not currently used, this is too slow.
    """
    # ...............................................
    def get_itis_taxon(self, namestr):
        ioutput = ItisAPI.match_name(namestr)
        return ioutput

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_parse=True, **kwargs):
        """Get ITIS accepted taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            kwargs: additional keyword arguments - to be ignored
        Return:
            a dictionary containing a count and list of dictionaries of 
                ITIS records corresponding to names in the ITIS taxonomy
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_parse=gbif_parse)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online('S^n Name resolution is online')
        else:
            return self.get_itis_taxon(namestr)

# .............................................................................
@cherrypy.expose
class ITISSolrName(_NameSvc):
    
    # ...............................................
    def get_itis_accepted_taxon(self, namestr, status, kingdom):
        ioutput = ItisAPI.match_name_solr(
            namestr, status=status, kingdom=kingdom)
        return ioutput

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_parse=False, status=None, kingdom=None, **kwargs):
        """Get ITIS accepted taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            status: filter records on status (TODO)
            kingdom: filter records on kingdom (TODO)
            kwargs: additional keyword arguments - to be ignored
        Return:
            a dictionary containing a count and list of dictionaries of 
                ITIS records corresponding to names in the ITIS taxonomy

        Todo:
            Find ITIS status strings
            Test parameters/boolean
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_parse=gbif_parse)
        namestr = usr_params['namestr']
        if not namestr:
            return {'spcoco.message': 'S^n Name resolution is online'}
        else:
            return self.get_itis_accepted_taxon(
                namestr, usr_params['status'], usr_params['kingdom'])

# .............................................................................
@cherrypy.expose
class NameTentaclesSvc(_NameSvc):
    # ...............................................
    def get_records(self, namestr, gbif_status, gbif_count ,status, kingdom):
        all_output = {}
            
        # GBIF Taxon Record
        gacc = GAcName()
        goutput = gacc.get_gbif_matching_taxon(namestr, gbif_status, gbif_count)
        all_output['GBIF Records'] = goutput
        
        # ITIS Solr Taxon Record
        itis = ITISSolrName()
        isoutput = itis.get_itis_accepted_taxon(namestr, status, kingdom)
        all_output['ITIS Solr Taxon Records'] = isoutput
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, status=None, kingdom=None, **kwargs):
        """Get one or more taxon records for a scientific name string from each
        available name service.
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
            gbif_count=gbif_count, status=status, kingdom=kingdom)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online('S^n Name tentacles are online')
        else:
            return self.get_records(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'],
                usr_params['status'], usr_params['kingdom'])

# .............................................................................
if __name__ == '__main__':
    # test    
    for namestr in TST_VALUES.NAMES:        
        print('Name = {}'.format(namestr))
        
        s2napi = NameTentaclesSvc()
        all_output  = s2napi.GET(
            namestr=namestr, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, status=None, kingdom=None)
        
        for svc, one_output in all_output.items():
            print('  {}:'.format(svc))
#             for k, v in one_output.items():
#                 print('  {}: {}'.format(k, v))
            print('')