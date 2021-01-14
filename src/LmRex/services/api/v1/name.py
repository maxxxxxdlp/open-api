import cherrypy

from LmRex.common.lmconstants import (ServiceProvider, APIService, TST_VALUES)
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
            return self._show_online()
        else:
            return self.get_gbif_matching_taxon(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'])

# .............................................................................
@cherrypy.expose
class NameITIS(_NameSvc):
    """
    Note:
        Not currently used, this is too slow.
    """
    PROVIDER = ServiceProvider.ITISWebService
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
            return self._show_online()
        else:
            return self.get_itis_taxon(namestr)

# .............................................................................
@cherrypy.expose
class NameITISSolr(_NameSvc):
    PROVIDER = ServiceProvider.ITISSolr
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
class NameTentacles(_NameSvc):
    # ...............................................
    def get_records(self, namestr, gbif_status, gbif_count ,status, kingdom):
            
        # GBIF Taxon Record
        gacc = NameGBIF()
        goutput = gacc.get_gbif_matching_taxon(namestr, gbif_status, gbif_count)
        all_output[ServiceProvider.GBIF['name']] = goutput
        
        # ITIS Solr Taxon Record
        itis = NameITISSolr()
        isoutput = itis.get_itis_accepted_taxon(namestr, status, kingdom)
        all_output[ServiceProvider.ITISSolr['name'] = isoutput
        
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
            return self._show_online()
        else:
            return self.get_records(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'],
                usr_params['status'], usr_params['kingdom'])

# .............................................................................
if __name__ == '__main__':
    # test    
    for namestr in TST_VALUES.NAMES[:3]:
        print('Name = {}'.format(namestr))
        
        s2napi = NameTentacles()
        all_output  = s2napi.GET(
            namestr=namestr, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, status=None, kingdom=None)
        
        for svc, one_output in all_output.items():
            print('  {}:'.format(svc))
            for k, v in one_output.items():
                print('  {}: {}'.format(k, v))
            print('')