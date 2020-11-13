import cherrypy

from LmRex.tools.api import (GbifAPI, ItisAPI)

# .............................................................................
@cherrypy.expose
class GAcName:
    
    # ...............................................
    def get_gbif_accepted_taxon(self, namestr, kingdom=None):
        rec = GbifAPI.parse_name(namestr)
        try:
            can_name = rec['canonicalName']
        except:
            # Default to original namestring if parsing fails
            can_name = namestr
        good_names = GbifAPI.match_name(can_name, status='accepted')
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
@cherrypy.expose
class ITISName:
    
    # ...............................................
    def get_itis_taxon(self, namestr, status=None, kingdom=None):
        rec = GbifAPI.parse_name(namestr)
        try:
            can_name = rec['canonicalName']
        except:
            # Default to original namestring if parsing fails
            can_name = namestr
        good_names = ItisAPI.match_name(can_name, status=None, kingdom=None)
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
            return self.get_itis_taxon(namestr)

# .............................................................................
@cherrypy.expose
class ITISSolrName:
    
    # ...............................................
    def get_itis_accepted_taxon(self, namestr, status=None, kingdom=None):
        rec = GbifAPI.parse_name(namestr)
        try:
            can_name = rec['canonicalName']
        except:
            # Default to original namestring if parsing fails
            can_name = namestr
        good_names = ItisAPI.match_name_solr(can_name, status=None, kingdom=None)
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
            return self.get_itis_accepted_taxon(namestr)

# .............................................................................
@cherrypy.expose
class NameSvc:
    
    # ...............................................
    def _assemble_output(self, records, count_only):
        if count_only:
            svc_output = 0
        else:
            svc_output = []
        # Handle dict record/s as a list
        if isinstance(records, dict):
            records = [records]
        for rec in records:
            is_rec = True
            # Error/info records use 'spcoco.' prefix for all keys
            for k in rec.keys():
                if k.startswith('spcoco'):
                    is_rec = False
                    break
            # Do not count error/info records
            if count_only:
                if is_rec:
                    svc_output += 1
            # Return data and error/info records
            else:
                svc_output.append(rec)
        return svc_output
    
    # ...............................................
    def get_records(self, namestr, count_only):
        all_output = {}
            
        # GBIF Taxon Record
        gacc = GAcName()
        recs = gacc.get_gbif_accepted_taxon(namestr)
        all_output['GBIF Records'] = self._assemble_output(recs, count_only)
        # ITIS Taxon Record
        itis = ITISName()
        recs = itis.get_itis_taxon(namestr)
        all_output['ITIS Taxon Records'] = self._assemble_output(recs, count_only)
        return all_output


    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None):
        if namestr is None:
            return {'message': 'S^n name tentacles are online'}
        else:
            return self.get_records(namestr, True)

# .............................................................................
if __name__ == '__main__':
    cherrypy.tree.mount(
        NameSvc(), '/tentacles/name',
        {'/':
            {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}
         }
    )

    cherrypy.engine.start()
    cherrypy.engine.block()

