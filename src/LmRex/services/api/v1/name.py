import cherrypy

from LmRex.common.lmconstants import (
    S2N, ServiceProvider, APIService, TST_VALUES)
from LmRex.services.api.v1.base import _S2nService
from LmRex.tools.api import (GbifAPI, ItisAPI)


# .............................................................................
@cherrypy.expose
class _NameSvc(_S2nService):
    SERVICE_TYPE = APIService.Name    

# .............................................................................
@cherrypy.expose
class NameGBIF(_NameSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def get_gbif_matching_taxon(self, namestr, gbif_status, gbif_count):
        all_output = {}
        # Get name from Gbif        
        output1 = GbifAPI.match_name(namestr, status=gbif_status)
        try:        
            good_names = output1[S2N.RECORDS_KEY]
        except:
            good_names = []
        # Add occurrence count to name records
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
                    namerec['occurrence_url'] = output2['occurrence_url']
        # Assemble output
        for key in [
            S2N.COUNT_KEY, S2N.RECORD_FORMAT_KEY, S2N.NAME_KEY,
            S2N.PROVIDER_KEY, S2N.ERRORS_KEY]:
            all_output[key] = output1[key]
            
        all_output[S2N.PROVIDER_QUERY_KEY] = [
            output1[S2N.PROVIDER_QUERY_KEY], output2[S2N.PROVIDER_QUERY_KEY]]
        all_output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        all_output[S2N.RECORDS_KEY] = good_names
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_accepted=True, gbif_count=True, **kwargs):
        """Get GBIF taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_accepted: flag to indicate whether to limit to 'valid' or 
                'accepted' taxa in the GBIF Backbone Taxonomy
            gbif_count: flag to indicate whether to count GBIF occurrences of 
                this taxon
            kwargs: any additional keyword arguments are ignored
            
        Return:
            a dictionary containing a count and list of dictionaries of 
                GBIF records corresponding to names in the GBIF backbone 
                taxonomy
                
        Note: gbif_parse flag to parse a scientific name into canonical name is 
            unnecessary for this method, as GBIF's match service finds the closest
            match regardless of whether author and date are included
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_accepted=gbif_accepted, gbif_count=gbif_count)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online()
        else:
            return self.get_gbif_matching_taxon(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'])

# # .............................................................................
# @cherrypy.expose
# class NameITIS(_NameSvc):
#     """
#     Note:
#         Not currently used, this is too slow.
#     """
#     # ...............................................
#     def get_itis_taxon(self, namestr):
#         output = ItisAPI.match_name(namestr)
#         output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
#         return output
# 
#     # ...............................................
#     @cherrypy.tools.json_out()
#     def GET(self, namestr=None, gbif_parse=True, **kwargs):
#         """Get ITIS accepted taxon records for a scientific name string
#         
#         Args:
#             namestr: a scientific name
#             gbif_parse: flag to indicate whether to first use the GBIF parser 
#                 to parse a scientific name into canonical name 
#             kwargs: any additional keyword arguments are ignored
#         Return:
#             a dictionary containing a count and list of dictionaries of 
#                 ITIS records corresponding to names in the ITIS taxonomy
#         """
#         usr_params = self._standardize_params(
#             namestr=namestr, gbif_parse=gbif_parse)
#         namestr = usr_params['namestr']
#         if not namestr:
#             return self._show_online()
#         else:
#             return self.get_itis_taxon(namestr)

# .............................................................................
@cherrypy.expose
class NameITISSolr(_NameSvc):
    PROVIDER = ServiceProvider.ITISSolr
    # ...............................................
    def get_itis_accepted_taxon(self, namestr, itis_accepted, kingdom):
        output = ItisAPI.match_name(
            namestr, itis_accepted=itis_accepted, kingdom=kingdom)
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_parse=True, itis_accepted=None, 
            kingdom=None, **kwargs):
        """Get ITIS accepted taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            itis_accepted: flag to indicate whether to limit to 'valid' or 
                'accepted' taxa in the ITIS Taxonomy
            kingdom: not yet implemented
            kwargs: any additional keyword arguments are ignored
            
        Return:
            a dictionary containing a count and list of dictionaries of 
                ITIS records corresponding to names in the ITIS taxonomy

        Todo:
            Filter on kingdom
        """
        usr_params = self._standardize_params(
            namestr=namestr, itis_accepted=itis_accepted, gbif_parse=gbif_parse)
        namestr = usr_params['namestr']
        if not namestr:
            return {'spcoco.message': 'S^n Name resolution is online'}
        else:
            return self.get_itis_accepted_taxon(
                namestr, usr_params['itis_accepted'], usr_params['kingdom'])

# .............................................................................
@cherrypy.expose
class NameTentacles(_NameSvc):
    PROVIDER = None
    # ...............................................
    def get_records(self, usr_params):
        all_output = {}
        # GBIF Taxon Record
        gacc = NameGBIF()
        goutput = gacc.get_gbif_matching_taxon(
            usr_params['namestr'], usr_params['gbif_status'], 
            usr_params['gbif_count'])
        all_output[ServiceProvider.GBIF['name']] = goutput
        
        # ITIS Solr Taxon Record
        itis = NameITISSolr()
        isoutput = itis.get_itis_accepted_taxon(
            usr_params['namestr'], usr_params['itis_accepted'], 
            usr_params['kingdom'])
        all_output[ServiceProvider.ITISSolr['name']] = isoutput
        
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, itis_accepted=None, kingdom=None, **kwargs):
        """Get one or more taxon records for a scientific name string from each
        available name service.
        
        Args:
            namestr: a scientific name
            gbif_accepted: flag to indicate whether to limit to 'valid' or 
                'accepted' taxa in the GBIF Backbone Taxonomy
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name
            gbif_count: flag to indicate whether to count GBIF occurrences of 
                this taxon
            itis_accepted: flag to indicate whether to limit to 'valid' or 
                'accepted' taxa in the ITIS Taxonomy
            kingdom: not yet implemented
            kwargs: any additional keyword arguments are ignored

        Return:
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
            gbif_count=gbif_count, itis_accepted=itis_accepted, kingdom=kingdom)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online()
        else:
            return self.get_records(usr_params)

# .............................................................................
if __name__ == '__main__':
    # test    
    for namestr in TST_VALUES.NAMES[:3]:
        for gparse in [False]:
            print('Name = {}  GBIF parse = {}'.format(namestr, gparse))
            s2napi = NameTentacles()
            all_output  = s2napi.GET(
                namestr=namestr, gbif_accepted=True, gbif_parse=gparse, 
                gbif_count=True, itis_accepted=True, kingdom=None)
              
            for svc, one_output in all_output.items():
                for k, v in one_output.items():
                    print('  {}: {}'.format(k, v))
                for key in S2N.required_for_namesvc_keys():
                    try:
                        one_output[key]
                    except:
                        if (len(one_output(S2N.ERRORS_KEY)) > 0 and 
                            one_output(S2N.COUNT_KEY) == 0):
                            pass
                        else:
                            print('Missing `{}` output element'.format(key))
                print('')
#
#             api = NameGBIF()
#             std_output  = api.GET(
#                 namestr=namestr, gbif_accepted=True, gbif_parse=gparse, 
#                 gbif_count=True)
#              
#             for k, v in std_output.items():
#                 print('  {}: {}'.format(k, v))
#             print('')

        
#             iapi = NameITISSolr()
#             iout = iapi.GET(
#                 namestr=namestr, gbif_parse=gparse, itis_accepted=True, kingdom=None)
#             print('  S2n ITIS Solr GET')
#             for k, v in iout.items():
#                 print('  {}: {}'.format(k, v))
#             print('')
