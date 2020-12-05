import cherrypy

from LmRex.common.lmconstants import Lifemapper
from LmRex.services.api.v1.name import GAcName
from LmRex.tools.api import LifemapperAPI

# .............................................................................
@cherrypy.expose
class LmMap:
    # ...............................................
    def get_sdmproject_with_urls(self, namestr, scenariocode, height, width):
        output = {'count': 0, 'records': []}
        # Lifemapper only uses GBIF Backbone Taxonomy accepted names
        gan = GAcName()
        goutput = gan.GET(
            namestr=namestr, gbif_accepted=True, do_count=False, do_parse=True)
        good_names = goutput['records']
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
        records = []
        for sname in scinames:
            # Step 1, get projection atoms
            atom_output = LifemapperAPI.find_sdmprojections_by_name(
                sname, prjscenariocode=scenariocode)
            atoms = atom_output['records']
            for atom in atoms:
                prjid = atom['id']
                # Step 2, use full projection records with constructed map url
                lmoutput = LifemapperAPI.get_sdmprojections_with_map(
                    prjid, height=height, width=width)
                try:
                    output['error'] = lmoutput['error']
                except:
                    pass
                # Add to output
                # TODO: make sure these include projection displayName
                records.extend(lmoutput['records'])
        output['records'] = records
        output['count'] = len(records)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, scenariocode=Lifemapper.OBSERVED_SCENARIO_CODE, 
            height=300, width=600):
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
            
        TODO: extend keyword parameters with other WMS options
        """
        if namestr is None:
            return {'spcoco.message': 'S^n Lifemapper mapper is online'}
        else:
            return self.get_sdmproject_with_urls(
                namestr, scenariocode, height, width)

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
#     Phlox longifolia Nutt., 2927725
    names = TST_VALUES.NAMES[0:2]
    for namestr in names:
        print('Name = {}'.format(namestr))
        
        lmapi = LmMap()
        output = lmapi.GET(namestr)
        for k, v in output.items():
            print('  {}: {}'.format(k, v))
