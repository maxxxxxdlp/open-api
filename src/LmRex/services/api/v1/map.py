import cherrypy

from LmRex.common.lmconstants import (
    ServiceProvider, APIService, Lifemapper, TST_VALUES)
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.name import NameGBIF
from LmRex.services.api.v1.s2n_type import (S2nKey, S2nOutput, print_s2n_output)
from LmRex.tools.provider.itis import ItisAPI
from LmRex.tools.provider.lifemapper import LifemapperAPI

# .............................................................................
@cherrypy.expose
class _MapSvc(_S2nService):
    SERVICE_TYPE = APIService.Map
    
# .............................................................................
@cherrypy.expose
class MapLM(_MapSvc):
    PROVIDER = ServiceProvider.Lifemapper

    # ...............................................
    def get_map_layers(self, namestr, scenariocode, color, do_match):
        # Lifemapper only uses GBIF Backbone Taxonomy accepted names
        if do_match is False:
            scinames = [namestr] 
        else:
            gan = NameGBIF()
            gout = gan.GET(
                namestr=namestr, gbif_accepted=True, do_count=False, do_parse=True)
            good_names = gout.records
            # Lifemapper uses GBIF Backbone Taxonomy accepted names
            # If none, try provided namestr
            scinames = []        
            if len(good_names) == 0:
                scinames.append(namestr)
            else:
                for namerec in good_names:
                    try:
                        scinames.append(namerec['scientificName'])
                    except Exception as e:
                        print('No scientificName element in GBIF record {} for {}'
                              .format(namerec, namestr))
        # 2-step until LM returns full objects
        stdrecs = []
        errmsgs = []
        queries = []
        for sname in scinames:
            # Step 1, get projections
            lout = LifemapperAPI.find_map_layers_by_name(
                sname, prjscenariocode=scenariocode, color=color)
            stdrecs.extend(lout.records)
            errmsgs.extend(lout.errors)
            queries.extend(lout.provider_query)
        
        full_out = S2nOutput(
            count=len(stdrecs), record_format=Lifemapper.RECORD_FORMAT_MAP, 
            records=stdrecs, provider=lout.provider, errors=errmsgs, 
            provider_query=queries, query_term=namestr, 
            service=self.SERVICE_TYPE)
        return full_out

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, scenariocode=Lifemapper.OBSERVED_SCENARIO_CODE, 
            color=None, do_match=True, **kwargs):
        """Get GBIF taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            color: one of a defined set of color choices for projection display 
            kwargs: additional keyword arguments - to be ignored

        Return:
            LmRex.services.api.v1.S2nOutput object with records as a 
            list of dictionaries of Lifemapper records corresponding to 
            maps with URLs and their layers in the Lifemapper archive
            
        Todo: 
            fix color parameter in Lifemapper WMS service
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, scenariocode=scenariocode, color=color, 
                do_match=do_match)
            namestr = usr_params['namestr']
            if not namestr:
                return self._show_online()
            else:
                return self.get_map_layers(
                    namestr,  usr_params['scenariocode'], usr_params['color'], 
                    usr_params['do_match'])
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])

# .............................................................................
@cherrypy.expose
class MapBISON(_MapSvc):
    """
    Note: unfinished
    """
    PROVIDER = ServiceProvider.BISON
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
            LmRex.services.api.v1.S2nOutput object with records as a 
            list of dictionaries of BISON records corresponding to 
            maps with URLs and their layers in the BISON database
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, gbif_parse=gbif_parse)
            namestr = usr_params['namestr']
            if not namestr:
                return self._show_online()
            else:
                return self.get_itis_taxon(namestr)
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])


# .............................................................................
@cherrypy.expose
class MapTentacles(_MapSvc):
    # ...............................................
    def get_records(self, namestr, gbif_status, gbif_count ,status, kingdom):
        all_output = {S2nKey.COUNT: 0, S2nKey.RECORDS: []}
#         all_output = S2nOutput(
#             count=0, records=[], query_term=namestr)
        # Lifemapper
        api = MapLM()
        try:
            lmoutput = api.get_gbif_matching_taxon(namestr, gbif_status, gbif_count)
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])
        else:
#             all_output.records.append(lmoutput)
            all_output[S2nKey.RECORDS].append(
            {ServiceProvider.Lifemapper[S2nKey.NAME]: lmoutput})
        # BISON
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
            LmRex.services.api.v1.S2nOutput object with records as a 
            list of dictionaries of Lifemapper records corresponding to 
            maps with URLs and their layers in the Lifemapper archive
        """
        try:
            usr_params = self._standardize_params(
                namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
                gbif_count=gbif_count, status=status, kingdom=kingdom)
            namestr = usr_params['namestr']
            if not namestr:
                return self._show_online()
            else:
                return self.get_records(
                    namestr, usr_params['gbif_status'], usr_params['gbif_count'],
                    usr_params['status'], usr_params['kingdom'])
        except Exception as e:
            return self.get_failure(query_term=namestr, errors=[e])

# .............................................................................
if __name__ == '__main__':
    # test    
#     Phlox longifolia Nutt., 2927725
    names = TST_VALUES.NAMES[0:2]
    for namestr in names:
        print('Name = {}'.format(namestr))
        
        lmapi = MapLM()
        out = lmapi.GET(namestr=namestr)
        print_s2n_output(out)
