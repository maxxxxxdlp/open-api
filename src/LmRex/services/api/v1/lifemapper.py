import cherrypy

from LmRex.services.api.v1.name import GAcName
from LmRex.tools.api import GbifAPI

# .............................................................................
@cherrypy.expose
class LmMap:
    # ...............................................
    def get_sdm_map(self, namestr):
        recs = []
        good_names = GbifAPI.match_name(namestr)

        for namerec in good_names:
            try:
                taxon_key = namerec['usageKey']
                sciname = namerec['scientificName']
            except Exception as e:
                print('Exception on {}: {}'.format(namestr, e))
                print('name = {}'.format(namerec))
            else:
                count, url = GbifAPI.count_accepted_name(taxon_key)
                recs.append({'scientificName': sciname, 'count': count, 'url': url})
        return recs

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True):
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
            return {'spcoco.message': 'S^n GBIF count-occurrences-for-name is online'}
        else:
            return self.get_gbif_count_for_taxon(namestr, do_parse)

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
#     Phlox longifolia Nutt., 2927725
    namestr = TST_VALUES.NAMES[0]
    print('Name = {}'.format(namestr))
    
    gapi = GAcName()
    do_parse = True
    grecs = gapi.get_gbif_accepted_taxon(namestr, do_parse)
    if len(grecs) == 1:
        

    iapi = ITISName()
    irecs = iapi.get_itis_taxon(namestr, do_parse)
        
    i2api = ITISSolrName()
    i2recs = i2api.get_itis_accepted_taxon(namestr, do_parse)

    napi = NameSvc()
    nrecs  = napi.get_records(namestr, do_parse)
    print('')
