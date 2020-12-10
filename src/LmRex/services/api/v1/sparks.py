import cherrypy

import LmRex.tools.solr as SpSolr

collection = 'spcoco'
solr_location = 'notyeti-192.lifemapper.org'

# .............................................................................
@cherrypy.expose
class SpecifyArk:
    """Query the Specify ARK resolver for a GUID"""

    # ...............................................
    @staticmethod
    def get_url_from_spark(solr_output):
        url = msg = None
        try:
            solr_doc = solr_output['docs'][0]
        except:
            pass
        else:
            # Get url from ARK for Specify query
            try:
                url = solr_doc['url']
            except Exception as e:
                pass
            else:
                if not url.startswith('http'):
                    msg = (
                        'Invalid URL {} returned from ARK for Specify record access'
                        .format(url))
                    url = None
        return (url, msg)
    
    # ...............................................
    def get_specify_arc_rec(self, occid):
        output = SpSolr.query_guid(collection, occid, solr_location=solr_location)
        return output

    # ...............................................
    def count_specify_arc_recs(self):
        return SpSolr.count_docs(collection, solr_location)

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



