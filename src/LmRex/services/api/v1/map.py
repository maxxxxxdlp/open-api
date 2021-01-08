import cherrypy

from LmRex.common.lmconstants import (ServiceProvider, APIService, TST_VALUES)
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.name import NameGBIF
from LmRex.tools.api import (LifemapperAPI, ItisAPI)



# .............................................................................
@cherrypy.expose
class _MapSvc(_S2nService):
    SERVICE_TYPE = APIService.Map
    
# .............................................................................
@cherrypy.expose
class MapLM(_MapSvc):
    PROVIDER = ServiceProvider.Lifemapper
    # ...............................................
    def get_map_info(
            self, namestr, scenariocode, bbox, color, height, 
            layers, frmat, request, srs, transparent, width, do_match):

        output = {'count': 0, 'records': []}
        # Lifemapper only uses GBIF Backbone Taxonomy accepted names
        if do_match is False:
            scinames = [namestr] 
        else:
            gan = NameGBIF()
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
                height=height, layers=layers, 
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
    def GET(self, namestr=None, scenariocode=None, 
            bbox=None, color=None, height=None, 
            layers=None, frmat=None, request=None, srs=None, 
            transparent=None, width=None, do_match=True, **kwargs):
        """Get GBIF taxon records for a scientific name string
        
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
            kwargs: additional keyword arguments - to be ignored
        Return:
            a list of dictionaries containing a matching name 
            (synonym, invalid, etc), record count, and query URL for retrieving 
            the records.
            
        Todo: 
            fix color parameter in Lifemapper WMS service
        """
        usr_params = self._standardize_params(
            namestr=namestr, scenariocode=scenariocode, bbox=bbox, color=color, 
            height=height, layers=layers, frmat=frmat, 
            request=request, srs=srs, transparent=transparent, width=width, 
            do_match=do_match)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online()
        else:
            return self.get_map_info(
                namestr, usr_params['scenariocode'], usr_params['bbox'], 
                usr_params['color'], usr_params['exceptions'], 
                usr_params['height'], usr_params['layers'], usr_params['format'], 
                usr_params['request'], usr_params['srs'], 
                usr_params['transparent'], usr_params['width'], 
                usr_params['do_match'])

# .............................................................................
@cherrypy.expose
class MapBISON(_MapSvc):
    """
    Note: unfinished
    """
    PROVIDER = ServiceProvider.BISON
    # ...............................................
    def get_itis_taxon(self, namestr):
        ioutput = ItisAPI.match_name(namestr)
        return ioutput

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_parse=True, **kwargs):
        """Get ITIS accepted taxon records for a scientific name string
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
            kwargs: additional keyword arguments - to be ignored
        Return:
            a dictionary containing asrc/LmRex/services/api/v1/ count and list of dictionaries of 
                ITIS records corresponding to names in the ITIS taxonomy
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_parse=gbif_parse)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online()
        else:
            return self.get_itis_taxon(namestr)


# .............................................................................
@cherrypy.expose
class MapTentacles(_MapSvc):
    # ...............................................
    def get_records(self, namestr, gbif_status, gbif_count ,status, kingdom):
        all_output = {}
            
        # Lifemapper
        gacc = MapLM()
        goutput = gacc.get_gbif_matching_taxon(namestr, gbif_status, gbif_count)
        all_output['Lifemapper'] = goutput
        
        # BISON
        return all_output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, gbif_accepted=True, gbif_parse=True, 
            gbif_count=True, status=None, kingdom=None, **kwargs):
        """Get one or more taxon records for a scientific name string from each
        available name service.
        
        Args:
            namestr: a scientific name
            gbif_parse: flag to indicate whether to first use the GBIF parser 
                to parse a scientific name into canonical name 
        Return:
            a dictionary with keys for each service queried.  Values contain 
                either a list of dictionaries/records returned for that service 
                or a count.
        """
        usr_params = self._standardize_params(
            namestr=namestr, gbif_accepted=gbif_accepted, gbif_parse=gbif_parse, 
            gbif_count=gbif_count, status=status, kingdom=kingdom)
        namestr = usr_params['namestr']
        if not namestr:
            return self._show_online()
        else:
            return self.get_records(
                namestr, usr_params['gbif_status'], usr_params['gbif_count'],
                usr_params['status'], usr_params['kingdom'])

# .............................................................................
if __name__ == '__main__':
    # test    
#     Phlox longifolia Nutt., 2927725
    names = TST_VALUES.NAMES[0:2]
    for namestr in names:
        print('Name = {}'.format(namestr))
        
        lmapi = MapLM()
        output = lmapi.GET(namestr=namestr, layers='bmng,prj,occ')
        print('  count: {}'.format(output['count']))
        try:
            rec = output['records'][0]
        except:
            pass
        else:
            print('  map_url: {}, pointlyr: {}, backlyr: {}'.format(
                rec['map']['lmMapEndpoint'], rec['map']['pointLayerName'], 
                rec['map']['backgroundLayerName']))
