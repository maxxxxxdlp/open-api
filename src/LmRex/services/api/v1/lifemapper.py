import cherrypy

from LmRex.common.lmconstants import Lifemapper
from LmRex.services.api.v1.name import GAcName
from LmRex.tools.api import GbifAPI, LifemapperAPI

# .............................................................................
@cherrypy.expose
class LmMap:
    # ...............................................
    def get_sdmproject_map_url(
            self, namestr, scenariocode):
        recs = []
        good_names = GbifAPI.match_name(namestr)

        for namerec in good_names:
            try:
                sciname = namerec['scientificName']
            except Exception as e:
                print('Exception on {}: {}'.format(namestr, e))
                print('name = {}'.format(namerec))
            else:
                # 2-step until LM returns full objects
                atoms = LifemapperAPI.find_sdmprojections_by_name(
                    sciname, prjscenariocode=scenariocode)
                for atom in atoms:
                    prjid = atom['id']
                    rec = LifemapperAPI.get_sdmprojection_map(prjid)                    
        return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, scenariocode=Lifemapper.OBSERVED_SCENARIO_CODE):
        """Get the number of occurrence records for all names "matching" the
        given scientific name string.
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a matching name 
            (synonym, invalid, etc), record count, and query URL for retrieving 
            the records.
        """
        if namestr is None:
            return {'spcoco.message': 'S^n Lifemapper mapper is online'}
        else:
            return self.get_sdmproject_map_url(namestr, scenariocode)

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
#     Phlox longifolia Nutt., 2927725
    namestr = TST_VALUES.NAMES[0]
    print('Name = {}'.format(namestr))
    
    lmapi = LmMap()
    lmapi.GET(namestr)
    
