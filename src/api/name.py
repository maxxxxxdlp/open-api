import cherrypy

from LmRex.tools.api import (GbifAPI, ItisAPI)


# .............................................................................
@cherrypy.expose
class GNameCount:
    # ...............................................
    def get_gbif_count_for_taxon(self, namestr, do_parse):
        recs = []
        gan = GAcName()
        good_names = gan.get_gbif_accepted_taxon(namestr, do_parse)
        for name in good_names:
            taxon_key = name['usageKey']
            sciname = name['scientificName']
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
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_gbif_count_for_taxon(namestr, do_parse)


# .............................................................................
@cherrypy.expose
class GAcName:
    
    # ...............................................
    def get_gbif_accepted_taxon(self, namestr, do_parse):
        if do_parse:
            rec = GbifAPI.parse_name(namestr)
            try:
                namestr = rec['canonicalName']
            except:
                # Default to original namestring if parsing fails
                pass
        good_names = GbifAPI.match_name(namestr, status='accepted')
        if len(good_names) == 0:
            return {'spcoco.error': 
                    'No matching GBIF taxon records for {}'.format(namestr)}
        else:
            return good_names

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True):
        """Get a one GBIF accepted taxon record for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or GBIF record 
            corresponding to a name in the GBIF backbone taxonomy
        """
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_gbif_accepted_taxon(namestr, do_parse)

# .............................................................................
@cherrypy.expose
class ITISName:
    
    # ...............................................
    def get_itis_taxon(self, namestr, do_parse):
        if do_parse:
            rec = GbifAPI.parse_name(namestr)
            try:
                namestr = rec['canonicalName']
            except:
                # Default to original namestring if parsing fails
                pass
        good_names = ItisAPI.match_name(namestr)
        if len(good_names) == 0:
            return {'spcoco.error': 
                    'No matching ITIS taxon records for {}'.format(namestr)}
        else:
            return good_names

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True):
        """Get one or more ITIS taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or ITIS record 
            corresponding to a name in the ITIS taxonomy
        """
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
        rec = GbifAPI.parse_name(namestr)
        try:
            namestr = rec['canonicalName']
        except:
            # Default to original namestring if parsing fails
            pass
        good_names = ItisAPI.match_name_solr(
            namestr, status=status, kingdom=kingdom)
        if len(good_names) == 0:
            return {'spcoco.error': 
                    'No matching GBIF taxon records for {}'.format(namestr)}
        else:
            return good_names

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True, status=None, kingdom=None):
        """Get one or more ITIS taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            do_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a list of dictionaries containing a message or ITIS record 
            corresponding to a name in the ITIS taxonomy
        """
        if namestr is None:
            return {'spcoco.message': 'S^n GBIF name resolution is online'}
        else:
            return self.get_itis_accepted_taxon(
                namestr, do_parse, status=status, kingdom=kingdom)

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
    def get_records(self, namestr, do_parse, count_only=False):
        all_output = {}
            
        # GBIF Taxon Record
        gacc = GAcName()
        recs = gacc.get_gbif_accepted_taxon(namestr, do_parse)
        all_output['GBIF Records'] = self._assemble_output(recs, count_only)
        # ITIS Taxon Record
        itis = ITISName()
        recs = itis.get_itis_taxon(namestr, do_parse)
        all_output['ITIS WS Taxon Records'] = self._assemble_output(
            recs, count_only)
        # ITIS Solr Taxon Record
        itis = ITISSolrName()
        recs = itis.get_itis_accepted_taxon(namestr, do_parse)
        all_output['ITIS Solr Taxon Records'] = self._assemble_output(
            recs, count_only)
        return all_output


    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, do_parse=True, count_only=False):
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
        if namestr is None:
            return {'message': 'S^n name tentacles are online'}
        else:
            return self.get_records(namestr, do_parse, count_only=count_only)

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    for namestr in TST_VALUES.NAMES:
        do_parse = True
        print('Name = {}'.format(namestr))
        gapi = GNameCount()
        grecs = gapi.get_gbif_count_for_taxon(namestr, do_parse)
        
        rec = GbifAPI.parse_name(namestr)
        try:
            namestr = rec['canonicalName']
            do_parse = False
        except:
            # Default to original namestring if parsing fails
            pass

        print('Parsed name = {}'.format(namestr))
        gapi = GAcName()
        grecs = gapi.get_gbif_accepted_taxon(namestr, do_parse)

        iapi = ITISName()
        irecs = iapi.get_itis_taxon(namestr, do_parse)
            
        i2api = ITISSolrName()
        i2recs = i2api.get_itis_accepted_taxon(namestr, do_parse)
    
        napi = NameSvc()
        nrecs  = napi.get_records(namestr, do_parse)
        print('')
