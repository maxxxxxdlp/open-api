import cherrypy

import LmRex.tools.solr as SpSolr

collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

# .............................................................................
@cherrypy.expose
class SpecifyArk:
    """Query the Specify ARK resolver for a GUID"""
    
    # ...............................................
    def get_specify_arc_rec(self, occid):
        rec = SpSolr.query_guid(collection, occid, solr_location=solr_location)
        if not rec:
            rec = {
                'spcoco.error': 
                'Failed to find ARK for Specify occurrence GUID {}'.format(occid)
                }
        return rec

    # ...............................................
    def count_specify_arc_recs(self):
        total = SpSolr.count_docs(collection, solr_location)
        rec = {'spcoco.total': total} 
        return rec

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None):
        """Get a single Specify ARK record for a GUID or count the total number 
        of records
        
        Args:
            occid: a Specify occurrence GUID, from the occurrenceId field
        Return:
            a single dictionary with a
             * count of records in the resolver or a
             * Specify ARK record
        """
        if occid is None:
            return self.count_specify_arc_recs()
        else:
            return self.get_specify_arc_rec(occid)



