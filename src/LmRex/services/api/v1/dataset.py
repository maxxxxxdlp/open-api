import cherrypy

from LmRex.common.lmconstants import ServiceProvider, APIService
from LmRex.tools.api import (
    GbifAPI, BisonAPI)
from LmRex.services.api.v1.base import _S2nService
        
# .............................................................................
@cherrypy.expose
class _DatasetSvc(_S2nService):
    SERVICE_TYPE = APIService.Dataset

# .............................................................................
@cherrypy.expose
class DatasetGBIF(_DatasetSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def _get_records(self, dataset_key, count_only):
        # 'do_limit' limits the number of records returned to the GBIF limit
        output = GbifAPI.get_occurrences_by_dataset(
            dataset_key, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=None, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
            kwargs: additional keyword arguments - to be ignored
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        count_only = self._set_default(count_only, True)
        usr_params = self._standardize_params(
            dataset_key=dataset_key, count_only=count_only)
        dataset_key = usr_params['dataset_key']
        if not dataset_key:
            return {'spcoco.message': 'S^n GBIF dataset query is online'}
        else:
            return self._get_records(dataset_key, usr_params['count_only'])


# .............................................................................
@cherrypy.expose
class DatasetBISON(_DatasetSvc):
    PROVIDER = ServiceProvider.BISON
    # ...............................................
    def _get_records(self, namestr, count_only):
        # 'do_limit' limits the number of records returned to the GBIF limit
        output = BisonAPI.get_occurrences_by_name(
            namestr, count_only, do_limit=True)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, match_itis=True, count_only=None, **kwargs):
        """Get a one or more GBIF records for a Specify GUID or 
        info/error message.
        
        Args:
            dataset_key: a GBIF dataset GUID, from the DWCA metadata
            kwargs: additional keyword arguments - to be ignored
        Return:
            a list of dictionaries containing DWC records from the chosen
            dataset.  
        """
        count_only = self._set_default(count_only, True)
        usr_params = self._standardize_params(
            namestr=namestr, match_itis=match_itis, count_only=count_only)
        namestr = usr_params['namestr']
        if namestr is None:
            return self._show_online()
        else:
            return self._get_records(namestr, usr_params['count_only'])
    
# .............................................................................
@cherrypy.expose
class DatasetTentacles(_DatasetSvc):
    
    # ...............................................
    def _get_records(self, dsid, count_only):
        all_output = {}
        
        # GBIF copy/s of Specify Record
        dg = DatasetGBIF()
        gbif_output = dg.GET(dataset_key=dsid, count_only=count_only)
        all_output['GBIF Records'] = gbif_output
        
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, occid=None, count_only=None, **kwargs):
        count_only = self._set_default(count_only, True)
        usr_params = self._standardize_params(occid=occid, count_only=count_only)
        return self._get_records(usr_params['occid'], usr_params['count_only'])
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    count_only = False
    dsid = TST_VALUES.GUIDS_W_SPECIFY_ACCESS[0]
    
    s2napi = DatasetGBIF()
    gdoutput = s2napi.GET(dataset_key=dsid, count_only=True)
    print(gdoutput)
    print('')
    

