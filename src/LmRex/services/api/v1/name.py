import cherrypy

from LmRex.common.lmconstants import TST_VALUES
from LmRex.tools.api import (GbifAPI, ItisAPI)

# ...............................................
def convert_to_bool(obj):
    try:
        obj = obj.lower()
    except:
        pass
    if obj in (1, 'yes', 'true'):
        return True
    else:
        return False

# ...............................................
def parse_name_with_gbif(namestr):
    goutput = GbifAPI.parse_name(namestr)
    try:
        namestr = goutput['record']['canonicalName']
    except:
        # Default to original namestring if parsing fails
        pass
    return namestr

# .............................................................................
@cherrypy.expose
class GAcName:
    # ...............................................
    def get_gbif_matching_taxon(self, namestr, gbif_accepted, do_parse):
        output = {}
        if do_parse:
            namestr = parse_name_with_gbif(namestr)
        status = None
        if gbif_accepted:
            status = 'accepted'
        # Get name from Gbif
        
        moutput = GbifAPI.match_name(namestr, status=status)        
        good_names = moutput['records']
        output['count'] = moutput['count']
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
    def GET(self, namestr=None, gbif_accepted=True, do_parse=True, **kwargs):
        """Get a one GBIF accepted taxon record for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or GBIF record 
            corresponding to a name in the GBIF backbone taxonomy
        """
        do_parse = convert_to_bool(do_parse)
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_gbif_matching_taxon(namestr, gbif_accepted, do_parse)

# .............................................................................
@cherrypy.expose
class ITISName:
    """
    Note:
        Not currently used, this is too slow.
    """
    # ...............................................
    def get_itis_taxon(self, namestr, do_parse):
        if do_parse:
            namestr = parse_name_with_gbif(namestr)
        ioutput = ItisAPI.match_name(namestr)
        return ioutput

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True, **kwargs):
        """Get one or more ITIS taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or ITIS record 
            corresponding to a name in the ITIS taxonomy
        """
        do_parse = convert_to_bool(do_parse)
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_itis_taxon(namestr, do_parse)

# .............................................................................
@cherrypy.expose
class ITISSolrName:
    
    # ...............................................
    def get_itis_accepted_taxon(
            self, namestr, do_parse, status=None, kingdom=None):
        if do_parse is True:
            namestr = parse_name_with_gbif(namestr)
        ioutput = ItisAPI.match_name_solr(
            namestr, status=status, kingdom=kingdom)
        return ioutput

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=False, status=None, kingdom=None, **kwargs):
        """Get one or more ITIS taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or ITIS record 
            corresponding to a name in the ITIS taxonomy
        """
        do_parse = convert_to_bool(do_parse)
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_itis_accepted_taxon(
                namestr, do_parse, status=status, kingdom=kingdom)

# .............................................................................
@cherrypy.expose
class NameSvc:   
    # ...............................................
    def get_records(self, namestr, do_parse):
        all_output = {}
            
        # GBIF Taxon Record
        gacc = GAcName()
        goutput = gacc.GET(namestr=namestr, do_parse=do_parse)
        all_output['GBIF Records'] = goutput
        # ITIS Solr Taxon Record
        itis = ITISSolrName()
        isoutput = itis.GET(namestr=namestr, do_parse=do_parse)
        all_output['ITIS Solr Taxon Records'] = isoutput
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=False, **kwargs):
        """Get one or more taxon records for a scientific name string from each
        available name service.
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            count_only: flag to indicate whether to return full results or 
                record counts for each service
        Return:
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        do_parse = convert_to_bool(do_parse)
        if namestr is None:
            return {'message': 'S^n name tentacles are online'}
        else:
            return self.get_records(namestr, do_parse)

# .............................................................................
if __name__ == '__main__':
    # test    
    for namestr in TST_VALUES.NAMES:
        do_parse = False
        
        print('Name = {}'.format(namestr))
        namestr = parse_name_with_gbif(namestr)
        print('Parsed name = {}'.format(namestr))
        
        s2napi = NameSvc()
        noutput  = s2napi.GET(namestr=namestr, do_parse=do_parse)
        for k, v in noutput.items():
            print('  {}: {}'.format(k, v))
        print('')
