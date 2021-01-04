from LmRex.tools.api import (GbifAPI, ItisAPI)

# .............................................................................
class S2nService:
    """
    Base S-to-the-N service, handles parameter names and value types
    """
    # ...............................................
    def parse_name_with_gbif(self, namestr):
        output = GbifAPI.parse_name(namestr)
        try:
            namestr = output['record']['canonicalName']
        except:
            # Default to original namestring if parsing fails
            pass
        return namestr

    # ...............................................
    def match_name_with_itis(self, namestr):
        output = ItisAPI.match_name_solr(namestr, status='valid')
        try:
            namestr = output['records'][0]['nameWOInd']
        except:
            # Default to original namestring if match fails
            pass
        return namestr
        
    # ...............................................
    def _fix_type(self, usr_val, default_val):
        # all strings are lower case
        try:
            usr_val = usr_val.lower()
        except:
            pass
        # Test membership in value options
        if isinstance(default_val, list):
            if usr_val not in default_val:
                usr_val = None
        elif isinstance(default_val, tuple):
            if len(default_val) == 2 and None in default_val:
                ex_val = default_val[0]
                if ex_val is None:
                    ex_val = default_val[1]
                if not isinstance(usr_val, type(ex_val)):
                    usr_val = None
            else:
                usr_val = None
        # Convert int, str to boolean
        elif isinstance(default_val, bool):                
            if usr_val in (0, '0', 'no', 'false'):
                return False
            else:
                return True
        elif isinstance(default_val, str):                
            usr_val = str(usr_val)
        # Values that cannot be converted correctly are changed to default value
        elif isinstance(default_val, float):
            try:             
                usr_val = float(usr_val)
            except:
                usr_val = default_val
        elif isinstance(default_val, int):                
            try:             
                usr_val = int(usr_val)
            except:
                usr_val = default_val
        return usr_val

    # ...............................................
    def _get_def_val(self, default_val):
        # Default val in value options is first
        if isinstance(default_val, list):
            def_val = default_val[0]
        elif isinstance(default_val, tuple):
            def_val = None
        else:
            def_val = default_val
        return def_val

        
    # ...............................................
    def _process_params(self, kwarg_defaults, user_kwargs):
        """
        Modify all user provided key/value pairs to change keys to lower case, 
        and change values to the expected type (string, int, float, boolean).
        
        Args:
            kwarg_defaults: dictionary of 
                * keys containing valid keyword parameters for the current 
                    service. All must be lowercase.
                * values containing 
                    * the default value or 
                    * list of valid values (first is default), or
                    * tuple of 2 elements: None (default), and a value of the correct type 
            user_kwargs: dictionary of keywords and values sent by the user for 
                the current service.
                
        Note:
            A list of valid values for a keyword can include None as a default 
                if user-provided value is invalid
        """
        good_params = {}
        # Correct all parameter keys/values present
        for key, val in user_kwargs.items():
            key = key.lower()
            try:
                ptype = kwarg_defaults[key]
            except:
                pass
            else:
                val = self._fix_type(val, ptype)
                good_params[key] = val
        # Add missing defaults
        for dkey, dval in kwarg_defaults.items():
            try:
                good_params[dkey]
            except:
                good_params[dkey] = self._get_def_val(dval)
        return good_params

    # ...............................................
#     @cherrypy.tools.json_out()
    def _standardize_params(
            self, namestr=None, gbif_accepted=False, gbif_parse=False,  
            gbif_count=False, itis_match=False, status=None, kingdom=None, 
            occid=None, dataset_key=None, count_only=True, url=None):
        """
        Standardize the parameters for all Name Services into a dictionary with 
        all keys as standardized parameter names and values as correctly-typed 
        user values or defaults. 
        
        Args:
            namestr: a scientific name
            gbif_accepted: flag to indicate whether to limit to "Accepted" 
                taxa in the GBIF Backbone Taxonomy
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name
            gbif_count: flag to indicate whether to count occurrences in 
                service provider for this taxon
            itis_match: flag to indicate whether to first use the ITIS solr 
                service to match a scientific name to an ITIS accepted name,
                used with BISON
            status: filter for ITIS records with this status
            kingdom: filter for ITIS records from this kingdom
            occid: a Specify occurrence GUID, mapped to the 
                dwc:occurrenceId field
            dataset_key: a GBIF dataset GUID for returning a set of points, 
                used with GBIF
            count_only: flag indicating whether to return records
            url: direct URL to Specify occurrence, only used with for Specify
                queries
        Return:
            a dictionary containing keys and properly formated values for the
                user specified parameters.
        """
        kwarg_defaults = {
            # For name services
            'namestr': (None, ''), 
            'gbif_accepted': False, 'gbif_parse': False, 'gbif_count': False, 
            'itis_match': False, 'status': (None, ''), 'kingdom': (None, ''),
            # For occurrence services
            'occid': (None, ''), 'dataset_key': (None, ''), 'count_only': False, 
            'url': (None, '')}
        user_kwargs = {
            'namestr': namestr, 'gbif_accepted': gbif_accepted, 
            'gbif_parse': gbif_parse, 'gbif_count': gbif_count, 
            'itis_match': itis_match, 'status': status, 'kingdom': kingdom, 
            'occid': occid, 'dataset_key': dataset_key, 
            'count_only': count_only, 'url': url}
        usr_params = self._process_params(kwarg_defaults, user_kwargs)
        # Remove 'gbif_accepted' flag and replace with 'gbif_status' filter for GBIF
        gbif_accepted = usr_params.pop('gbif_accepted')
        if gbif_accepted is True:
            usr_params['gbif_status'] = 'accepted'
        else:
            usr_params['gbif_status'] = None
        # Remove 'gbif_parse' and itis_match flags
        gbif_parse = usr_params.pop('gbif_parse')
        itis_match = usr_params.pop('itis_match')
        namestr = usr_params['namestr']
        # Replace namestr with GBIF-parsed namestr
        if namestr:
            if gbif_parse: 
                usr_params['namestr'] = self.parse_name_with_gbif(namestr)
            elif itis_match:
                usr_params['namestr'] = self.parse_name_with_gbif(namestr)
                
        return usr_params


# .............................................................................
if __name__ == '__main__':
    kwarg_defaults = {
        'count_only': False,
        'width': 600,
        'height': 300,
        'type': [],
        }