import cherrypy

from LmRex.common.lmconstants import (
    ServiceProvider, APIService, TST_VALUES)
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.s2n_type import (S2nKey, S2nOutput, print_s2n_output)
from LmRex.tools.provider.gbif import GbifAPI
from LmRex.tools.provider.itis import ItisAPI

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
#         all_output = {}
        # Get name from Gbif        
        out1 = GbifAPI.match_name(namestr, status=gbif_status)
        try:        
            good_names = out1.records
        except:
            good_names = []
        else:
            prov_query_list = out1.provider_query
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
                        outdict = GbifAPI.count_occurrences_for_taxon(taxon_key)
                        namerec[S2nKey.OCCURRENCE_COUNT] = outdict[S2nKey.COUNT]
                        namerec[S2nKey.OCCURRENCE_URL] = outdict[S2nKey.OCCURRENCE_URL]
                        prov_query_list.extend(outdict[S2nKey.PROVIDER_QUERY])
                        
        all_output = S2nOutput(
            count=out1.count, record_format=out1.record_format, 
            provider=out1.provider,errors=out1.errors, 
            records=good_names, provider_query=prov_query_list,
            query_term=namestr, service=self.SERVICE_TYPE)
        
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
            LmRex.services.api.v1.S2nOutput object with records as a list of 
            dictionaries of GBIF records corresponding to names in the GBIF 
            backbone taxonomy
                
        Note: gbif_parse flag to parse a scientific name into canonical name is 
            unnecessary for this method, as GBIF's match service finds the closest
            match regardless of whether author and date are included
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, gbif_accepted=gbif_accepted, gbif_count=gbif_count)
            namestr = usr_params['namestr']
            if not namestr:
                return self._show_online()
            else:
                return self.get_gbif_matching_taxon(
                    namestr, usr_params['gbif_status'], usr_params['gbif_count'])
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])

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
#         output[S2nKey.SERVICE] = self.SERVICE_TYPE
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
        out = ItisAPI.match_name(
            namestr, itis_accepted=itis_accepted, kingdom=kingdom)
        
        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=self.PROVIDER[S2nKey.NAME],
            errors=out.errors, provider_query=out.provider_query,
            query_term=namestr, service=APIService.Name)

        return full_out

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
            LmRex.services.api.v1.S2nOutput object with records as a list of 
            dictionaries of ITIS records corresponding to names in the ITIS 
            taxonomy

        Todo:
            Filter on kingdom
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, itis_accepted=itis_accepted, gbif_parse=gbif_parse)
            namestr = usr_params['namestr']
            if not namestr:
                return {'spcoco.message': 'S^n Name resolution is online'}
            else:
                return self.get_itis_accepted_taxon(
                    namestr, usr_params['itis_accepted'], usr_params['kingdom'])
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])

# .............................................................................
@cherrypy.expose
class NameTentacles(_NameSvc):
    PROVIDER = ServiceProvider.S2N
    # ...............................................
    def get_records(self, usr_params):
        allrecs = []
        
        # GBIF Taxon Record
        gacc = NameGBIF()
        goutput = gacc.get_gbif_matching_taxon(
            usr_params['namestr'], usr_params['gbif_status'], 
            usr_params['gbif_count'])
        allrecs.append(goutput)
        
        # ITIS Solr Taxon Record
        itis = NameITISSolr()
        isoutput = itis.get_itis_accepted_taxon(
            usr_params['namestr'], usr_params['itis_accepted'], 
            usr_params['kingdom'])
        allrecs.append(isoutput)

        full_out = S2nOutput(
            count=len(allrecs), records=allrecs, provider=self.PROVIDER,
            query_term=namestr, service=APIService.Name)
        return full_out

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
            LmRex.services.api.v1.S2nOutput object with records as a list of 
            dictionaries of records corresponding to names in the provider 
            taxonomy.
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
                gbif_count=gbif_count, itis_accepted=itis_accepted, kingdom=kingdom)
            namestr = usr_params['namestr']
            if not namestr:
                return self._show_online()
            else:
                return self.get_records(usr_params)
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])
#             return self.get_failure(
#                 count=0, record_format='', records=[], provider=self.PROVIDER, 
#                 errors=['{}'.format(e)], provider_query='', 
#                 service=self.SERVICE_TYPE)
# .............................................................................
if __name__ == '__main__':

    # test
    test_names = TST_VALUES.NAMES[:5]
    test_names.append(TST_VALUES.GUIDS_W_SPECIFY_ACCESS[0])
    
    test_names = ['Acer obtusifolium Sibthorp & Smith']
    for namestr in test_names:
        for gparse in [False]:
            print('Name = {}  GBIF parse = {}'.format(namestr, gparse))
            s2napi = NameTentacles()
            all_output  = s2napi.GET(
                namestr=namestr, gbif_accepted=False, gbif_parse=gparse, 
                gbif_count=True, itis_accepted=True, kingdom=None)
              
            for svc in all_output.records:
                print_s2n_output(svc)
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
