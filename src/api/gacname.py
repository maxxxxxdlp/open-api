import cherrypy

from LmRex.tools.api import GbifAPI

# .............................................................................
@cherrypy.expose
class GAcName:
    
    # ...............................................
    def get_gbif_accepted_taxon(self, namestr):
        [sci_name, can_name, kingdom] = GbifAPI.parse_name(namestr)
        if can_name is not None:    
            good_names = GbifAPI.match_accepted_name(can_name, kingdom=kingdom)
        if len(good_names) == 0:
            return {'spcoco.error': 
                    'No matching GBIF taxon records for {}'.format(namestr)}
        else:
            return good_names

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None):
        """Get a one GBIF accepted taxon record for a scientific name string
        
        Args:
            namestr: a scientific name
        Return:
            one dictionary containing a message or GBIF record corresponding 
            to the accepted name in the GBIF Backbone taxonomy
        """
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_gbif_accepted_taxon(namestr)

# .............................................................................
if __name__ == '__main__':
    cherrypy.tree.mount(
        GAcName(), '/api/gacname',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

