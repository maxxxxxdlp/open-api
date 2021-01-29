import typing

from LmRex.common.lmconstants import (
    APIService, Lifemapper, S2N, VALID_MAP_REQUESTS)
from LmRex.tools.api import (GbifAPI, ItisAPI)

RecordsList = typing.List[typing.Dict]

# Changed to TypedDict on update to Python 3.8+
class ProviderQuery(typing.NamedTuple):
    S2N.COUNT_KEY: int
    S2N.RECORD_FORMAT_KEY: str
    S2N.RECORDS_KEY: typing.List[typing.Dict]
    S2N.PROVIDER_KEY: str
    S2N.ERRORS_KEY: typing.List[str]
    S2N.PROVIDER_QUERY_KEY: typing.List[str]
    S2N.SERVICE_KEY: str
    label: str
    
"""
count    0
record_format    "https://www.gbif.org/developer/species"
name    "2c1becd5-e641-4e83-b3f5-76a55206539a"
provider    "GBIF"
errors    []
provider_query    
0    "http://api.gbif.org/v1/species/match?name=2c1becd5-e641-4e83-b3f5-76a55206539a&verbose=true"
service    "name"
records
"""
S2nOutput = typing.NewType
# .............................................................................
class _S2nService:
    """Base S-to-the-N service, handles parameter names and acceptable values"""
    # overridden by subclasses
    SERVICE_TYPE = None
    PROVIDER = None

    # .............................................................................
    @classmethod
    def endpoint(self):
        endpoint =  '{}/{}'.format(APIService.Root, self.SERVICE_TYPE)
        if self.PROVIDER is not None:
            endpoint = '{}/{}'.format(endpoint, self.PROVIDER['endpoint'])
        return endpoint

    # ...............................................
    def _set_default(self, param, default):
        if param is None:
            param = default
        return param
    
    # ...............................................
    def _show_online(self):
        try:
            msg = 'S^n {} {} service is online'.format(
                self.SERVICE_TYPE, self.PROVIDER['name'])
        except:
            msg = 'S^n {} service is online'.format(
                self.SERVICE_TYPE)
        return {'info': msg}

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
        output = ItisAPI.match_name(namestr, status='valid')
        try:
            namestr = output['records'][0]['nameWOInd']
        except:
            # Default to original namestring if match fails
            pass
        return namestr
        
    # ...............................................
    def _fix_type(self, provided_val, default_val):
        if provided_val is None:
            return None
        # all strings are lower case
        try:
            provided_val = provided_val.lower()
        except:
            pass
        
        # Find type from sequence of options
        if isinstance(default_val, list) or isinstance(default_val, tuple):
            if len(default_val) <= 1:
                raise Exception('Sequence of options must contain > 1 item')
            # Find type from other value in sequence containing None
            if default_val[0] is not None:
                default_val = default_val[0]
            else:
                default_val = default_val[1]

        # Convert int, str to boolean
        if isinstance(default_val, bool):                
            if provided_val in (0, '0', 'no', 'false'):
                return False
            else:
                return True
        elif isinstance(default_val, str):                
            usr_val = str(provided_val)
            
        # Failed conversions return default value
        elif isinstance(default_val, float):
            try:             
                usr_val = float(provided_val)
            except:
                usr_val = default_val
        elif isinstance(default_val, int):                
            try:             
                usr_val = int(provided_val)
            except:
                usr_val = default_val
                
        return usr_val

    # ...............................................
    def _get_def_val(self, default_val):
        # Sequences containing None have that as default value, or first value
        if isinstance(default_val, list) or isinstance(default_val, tuple):
            def_val = default_val[0]
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
        for key, provided_val in user_kwargs.items():
            key = key.lower()
            try:
                default_val = kwarg_defaults[key]
            except:
                pass
            else:
                usr_val = self._fix_type(provided_val, default_val)
                good_params[key] = usr_val
                
        # Add missing defaults
        for dkey, dval in kwarg_defaults.items():
            if good_params[dkey] is None:
                good_params[dkey] = self._get_def_val(dval)
        return good_params

    # ...............................................
#     @cherrypy.tools.json_out()
    def _standardize_params(
            self, namestr=None, gbif_accepted=False, gbif_parse=False,  
            gbif_count=False, itis_match=False, itis_accepted=False, kingdom=None, 
            occid=None, dataset_key=None, count_only=True, url=None,
            scenariocode=None, bbox=None, color=None, exceptions=None, height=None, 
            layers=None, request=None, frmat=None, srs=None, transparent=None, 
            width=None, do_match=True):
        """Standardize the parameters for all Name Services into a dictionary 
        with all keys as standardized parameter names and values as 
        correctly-typed user values or defaults. 
        
        Note: 
            This function sets default values, but defaults may be changed for 
            a few subclasses that share parameters but have different defaults.  
            Change default with _set_default, prior to calling this method.
        
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
            itis_accepted: flag to indicate whether to limit to 'valid' or 
                'accepted' taxa in the ITIS Taxonomy
            kingdom: filter for ITIS records from this kingdom
            occid: a Specify occurrence GUID, mapped to the 
                dwc:occurrenceId field
            dataset_key: a GBIF dataset GUID for returning a set of points, 
                used with GBIF
            count_only: flag indicating whether to return records
            url: direct URL to Specify occurrence, only used with for Specify
                queries
            scenariocode: A lifemapper code indicating the climate scenario used
                to calculate predicted presence of a species 
            bbox: A (min x, min y, max x, max y) tuple of bounding parameters
            color: The color (or color ramp) to use for the map
            exceptions: The format to report exceptions in
            height: The height (in pixels) of the returned map
            layers: A comma-delimited list of layer names
            request: The request operation name to perform
            frmat: The desired response format, query parameter is
                'format'
            sld: (todo) A URL referencing a StyledLayerDescriptor XML file which
                controls or enhances map layers and styling
            sld_body: (todo) A URL-encoded StyledLayerDescriptor XML document which
                controls or enhances map layers and styling
            srs: The spatial reference system for the map output.  'crs' for
                version 1.3.0.
            transparent: Boolean indicating if the background of the map should
                be transparent
            width: The width (in pixels) of the returned map
            do_match: Flag indicating whether to query GBIF for the 'accepted' 
                scientific name
        Return:
            a dictionary containing keys and properly formated values for the
                user specified parameters.
        """
        empty_str = ''
        kwarg_defaults = {
            # Sequences denote value options, the first is the default, 
            #    other values are of the required type
            # For name services
#             'namestr': (None, empty_str),
            'gbif_accepted': False, 
            'gbif_parse': False, 
            'gbif_count': False, 
            'itis_match': False, 
            'itis_accepted': False, 
            'kingdom': (None, empty_str),
            # For occurrence services
            'occid': (None, empty_str), 
            'dataset_key': (None, empty_str), 
            'count_only': False, 
            'url': (None, empty_str),
            'scenariocode': Lifemapper.valid_scenario_codes(),
            'bbox': '-180,-90,180,90', 
            'color': Lifemapper.VALID_COLORS,
#             'crs': (None, ''), 
            'exceptions': (None, empty_str), 
            'height': 300, 
            'layers': (None, 'prj', 'occ', 'bmng'),
            'request': VALID_MAP_REQUESTS, 
            'format': None, 
#             'service': 'wms',
#             'sld': None, 
#             'sld_body': None, 
            'srs': 'epsg:4326', 
#             'styles': None, 
            'transparent': None, 
#             'version': '1.0', 
            'width': 600,
            'do_match': True}
        user_kwargs = {
#             'namestr': namestr, 
            'gbif_accepted': gbif_accepted, 
            'gbif_parse': gbif_parse, 
            'gbif_count': gbif_count, 
            'itis_match': itis_match, 
            'itis_accepted': itis_accepted, 
            'kingdom': kingdom, 
            'occid': occid, 
            'dataset_key': dataset_key, 
            'count_only': count_only, 
            'url': url,
            'scenariocode': scenariocode,
            'bbox': bbox, 
            'color': color, 
            'exceptions': exceptions, 
            'height': height, 
            'layers': layers, 
            'request': request, 
            'format': frmat, 
            'srs': srs, 
            'transparent': transparent, 
            'width': width, 
            'do_match': do_match}
        usr_params = self._process_params(kwarg_defaults, user_kwargs)
        # Do not edit namestr, maintain capitalization
        usr_params['namestr'] = namestr
        # Remove 'gbif_accepted' flag and replace with 'gbif_status' filter for GBIF
        # GBIF Taxonomic Constants at:
        # https://gbif.github.io/gbif-api/apidocs/org/gbif/api/vocabulary/TaxonomicStatus.html
        gbif_accepted = usr_params.pop('gbif_accepted')
        if gbif_accepted is True:
            usr_params['gbif_status'] = 'accepted'
        else:
            usr_params['gbif_status'] = None
        # Remove 'gbif_parse' and itis_match flags
        gbif_parse = usr_params.pop('gbif_parse')
        itis_match = usr_params.pop('itis_match')
#         namestr = usr_params['namestr']
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