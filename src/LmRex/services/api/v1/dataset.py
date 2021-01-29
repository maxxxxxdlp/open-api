import cherrypy

from LmRex.common.lmconstants import S2N, ServiceProvider, APIService
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
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=None, **kwargs):
        """Get one or more occurrence records for a dataset identifier from the
        GBIF occurrence service.
        
        Args:
            dataset_key: a unique dataset identifier for a collection of 
                occurrence records.
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            A dictionary of metadata and a count of records found in GBIF and 
            an optional list of records.
                
        Note: 
            The dataset_key is an identifier assigned by GBIF to collections
            which publish their datasets to GBIF.
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
        output[S2N.SERVICE_KEY] = self.SERVICE_TYPE
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, namestr=None, match_itis=True, count_only=None, **kwargs):
        """Get one or more occurrence records for a dataset identifier from the
        BISON occurrence service.
        
        Args:
            dataset_key: a unique dataset identifier for a collection of 
                occurrence records.
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            A dictionary of metadata and a count of records found in BISON and 
            an optional list of records.
                
        Note: 
            The dataset_key is an identifier assigned by GBIF to collections
            which publish their datasets to GBIF.  BISON maintains this value 
            in records they retrieve from GBIF. 
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
    PROVIDER = None
    # ...............................................
    def _get_records(self, dsid, count_only):
        all_output = {S2N.COUNT_KEY: 0, S2N.RECORDS_KEY: []}
        
        # GBIF copy/s of Specify Record
        dg = DatasetGBIF()
        gbif_output = dg.GET(dataset_key=dsid, count_only=count_only)
        all_output['GBIF Records'] = gbif_output
        all_output[S2N.RECORDS_KEY].append(
            {ServiceProvider.GBIF[S2N.NAME_KEY]: gbif_output})
        
        return all_output

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=None, **kwargs):
        """Get one or more occurrence records for a dataset identifier from all
        available occurrence record services.
        
        Args:
            dataset_key: a unique dataset identifier for a collection of 
                occurrence records.
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            a dictionary with keys for each service queried.  Service values 
            contain metadata and a count of records found in that service and an 
            optional list of records.
                
        Note: 
            The dataset_key is an identifier assigned by GBIF to collections
            which publish their datasets to GBIF.  BISON maintains this value 
            in records they retrieve from GBIF. 
        """
        count_only = self._set_default(count_only, True)
        usr_params = self._standardize_params(
            dataset_key=dataset_key, count_only=count_only)
        return self._get_records(
            usr_params['dataset_key'], usr_params['count_only'])
        
# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    gocc = DatasetGBIF()
    for count_only in [True, False]:
        rkeys = S2N.required_for_datasetsvc_keys()
        if count_only is True:
            rkeys = S2N.required_for_datasetsvc_norecs_keys()

        gout = gocc.GET(
            TST_VALUES.DS_GUIDS_W_SPECIFY_ACCESS_RECS[0], count_only=count_only)
        print(gout)
            
        for key in rkeys:
            try:
                gout[key]
            except:
                print('Missing `{}` output element'.format(key))


