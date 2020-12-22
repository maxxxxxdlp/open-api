import cherrypy

from LmRex.common.lmconstants import Lifemapper
from LmRex.services.api.v1.base import S2nService
from LmRex.services.api.v1.name import GAcName
from LmRex.tools.api import LifemapperAPI

# .............................................................................
@cherrypy.expose
class WMSSvc(S2nService):

    # ...............................................
    def _standardize_params(
            self, bbox=None, color=None, exceptions=None, height=None, 
            layers=None, request=None, frmat=None, srs=None, transparent=None, 
            width=None, do_match=True):
        """
        Standardize the parameters for all Map Services into a dictionary with 
        all keys as standardized parameter names and values as correctly-typed 
        user values or defaults. 
        
        Args:
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
        kwarg_defaults = {
            'bbox': '-180,-90,180,90', 
            'color': [
                'red', 'gray', 'green', 'blue', 'safe', 'pretty', 'yellow', 
                'fuschia', 'aqua', 'bluered', 'bluegreen', 'greenred'],
#             'crs': (None, ''), 
            'exceptions': (None, ''), 
            'height': 300, 
            'layers': 'prj',
            'request': ['getmap', 'getlegendgraphic'], 
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
            'bbox': bbox, 'color': color, 'exceptions': exceptions, 
            'height': height, 'layers': layers, 'request': request, 
            'format': frmat, 'srs': srs, 'transparent': transparent, 
            'width': width}
        usr_params = self._process_params(kwarg_defaults, user_kwargs)
        return usr_params


# .............................................................................
@cherrypy.expose
class LmMap(WMSSvc):

    # ...............................................
    def get_sdmproject_with_urls(
            self, namestr, scenariocode, bbox, color, exceptions, height, 
            layers, frmat, request, srs, transparent, width, do_match):
        """
        Return metadata, including a map_url, for a Lifemapper SDM projection.
         
        Args:
            namestr: Scientific name for desired projection
            scenariocode: Lifemapper code for environmental layerset used 
                in projection.  Defaults to the code for observed data.
            bbox: A (min x, min y, max x, max y) tuple of bounding parameters
            color: The color (or color ramp) to use for the map
            exceptions: The format to report exceptions in
            height: The height (in pixels) of the returned map
            layers: A comma-delimited list of layer names
            request: The request operation name to perform
            frmat: The desired response format, query parameter is
                'format'
            srs: The spatial reference system for the map output.  'crs' for
                version 1.3.0.
            transparent: Boolean indicating if the background of the map should
                be transparent
            width: The width (in pixels) of the returned map
            do_match: Flag indicating whether to query GBIF for the 'accepted' 
                scientific name
        """
        output = {'count': 0, 'records': []}
        # Lifemapper only uses GBIF Backbone Taxonomy accepted names
        if do_match is False:
            scinames = [namestr] 
        else:
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
        msgs = []
        for sname in scinames:
            # Step 1, get projection atoms
            prj_output = LifemapperAPI.find_projections_by_name(
                sname, prjscenariocode=scenariocode, bbox=bbox, color=color, 
                exceptions=exceptions, height=height, layers=layers, 
                frmat=frmat, request=request, srs=srs,  transparent=transparent, 
                width=width)
            # Add to output
            # TODO: make sure these include projection displayName
            records.extend(prj_output['records'])
            for key in ['warning', 'error']:
                try:
                    msgs.append(prj_output[key])
                except:
                    pass
        if len(msgs) > 0:
            output['errors'] = msgs
        output['records'] = records
        output['count'] = len(records)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, scenariocode=Lifemapper.OBSERVED_SCENARIO_CODE, 
            bbox='-180,-90,180,90', color='red', exceptions=None, height=400, 
            layers='prj', frmat='png', request='getmap', srs='epsg:4326', 
            transparent=None, width=800, do_match=True):
        """Get the number of occurrence records for all names "matching" the
        given scientific name string.
        
        Args:
            namestr: a scientific name
            scenariocode: a Lifemapper projection scenario code, defaults to 
                projection based on observed (not predicted) environmental data
            bbox: bbox as a comma-delimited string, minX, minY, maxX, maxY
            color: one of a defined set of color choices for projection display 
            exceptions: format for exceptions
            height: height of the image
            layers: a comma-delimted string of layers, with codes for 
                projection ('prj'), occurrence points ('occ'), background 
                blue marble satellite image ('bmng')
            frmat: output format
            request: WMS request
            srs: Spatial reference system, defaults to epsg:4326 (geographic)
            transparent: transparency
            width: width of the image
        Return:
            a list of dictionaries containing a matching name 
            (synonym, invalid, etc), record count, and query URL for retrieving 
            the records.
            
        TODO: fix color parameter in Lifemapper WMS service
        """
        usr_params = self._standardize_params(
            bbox=bbox, color=color, exceptions=exceptions, height=height, 
            layers=layers, frmat=frmat, request=request, srs=srs, 
            transparent=transparent, width=width, do_match=do_match)
        if namestr is None:
            return {'spcoco.message': 'S^n Lifemapper mapper is online'}
        else:
            return self.get_sdmproject_with_urls(
                namestr, scenariocode, usr_params['bbox'], usr_params['color'], 
                usr_params['exceptions'], usr_params['height'], 
                usr_params['layers'], usr_params['format'], 
                usr_params['request'], usr_params['srs'], 
                usr_params['transparent'],  usr_params['width'], 
                usr_params['do_match'])

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
#     Phlox longifolia Nutt., 2927725
    names = TST_VALUES.NAMES[0:2]
    for namestr in names:
        print('Name = {}'.format(namestr))
        
        lmapi = LmMap()
        output = lmapi.GET(namestr=namestr, layers='bmng,prj,occ')
        print('  count: {}'.format(output['count']))
        try:
            rec = output['records'][0]
        except:
            pass
        else:
            print('  map_url: {}'.format(rec['map_url']))
