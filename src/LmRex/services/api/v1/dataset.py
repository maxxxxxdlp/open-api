import cherrypy

from LmRex.common.lmconstants import ServiceProvider, APIService
from LmRex.tools.provider.gbif import GbifAPI
from LmRex.tools.provider.bison import BisonAPI
from LmRex.services.api.v1.base import _S2nService
from LmRex.services.api.v1.s2n_type import S2nOutput, print_s2n_output       ,\
    S2nKey
        
# .............................................................................
@cherrypy.expose
class _DatasetSvc(_S2nService):
    SERVICE_TYPE = APIService.Dataset

# .............................................................................
@cherrypy.expose
class DatasetGBIF(_DatasetSvc):
    PROVIDER = ServiceProvider.GBIF
    # ...............................................
    def get_records(self, dataset_key, count_only):
        # 'do_limit' limits the number of records returned to the GBIF limit
        output = GbifAPI.get_occurrences_by_dataset(
            dataset_key, count_only)
        return output

    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dataset identifier from the
        GBIF occurrence service.
        
        Args:
            dataset_key: a unique dataset identifier for a collection of 
                occurrence records.
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of GBIF records corresponding to specimen 
            occurrences in the GBIF database
                
        Note: 
            If count_only=False, the records element will contain a subset of 
            records available for that dataset.  The number of records will be
            less than or equal to the paging limit set by the provider.  
        Note: 
            The dataset_key is an identifier assigned by GBIF to collections
            which publish their datasets to GBIF.
        """
        try:
            usr_params = self._standardize_params(
                dataset_key=dataset_key, count_only=count_only)
            dataset_key = usr_params['dataset_key']
            if not dataset_key:
                return {'spcoco.message': 'S^n GBIF dataset query is online'}
            else:
                return self.get_records(dataset_key, usr_params['count_only'])
        except Exception as e:
            return self.get_failure(query_term=dataset_key, errors=[str(e)])


# # .............................................................................
# @cherrypy.expose
# class DatasetBISON(_DatasetSvc):
#     PROVIDER = ServiceProvider.BISON
#     # ...............................................
#     def _get_records(self, dataset_key, count_only):
#         # 'do_limit' limits the number of records returned to the GBIF limit
#         output = BisonAPI.get_occurrences_by_dataset(
#             dataset_key, count_only, do_limit=True)
#         output[S2nKey.SERVICE] = self.SERVICE_TYPE
#         return output
# 
#     # ...............................................
#     @cherrypy.tools.json_out()
#     def GET(self, dataset_key=None, match_itis=True, count_only=False, **kwargs):
#         """Get one or more occurrence records for a dataset identifier from the
#         BISON occurrence service.
#         
#         Args:
#             dataset_key: a unique dataset identifier for a collection of 
#                 occurrence records.
#             count_only: flag to indicate whether to return only a count, or 
#                 a count and records
#             kwargs: any additional keyword arguments are ignored
# 
#         Return:
#             LmRex.services.api.v1.S2nOutput object with optional records as a 
#             list of dictionaries of BISON records corresponding to specimen 
#             occurrences in the BISON database
#                 
#         Note: 
#             If count_only=False, the records element will contain a subset of 
#             records available for that dataset.  The number of records will be
#             less than or equal to the paging limit set by the provider.  
#         Note: 
#             The dataset_key is an identifier assigned by GBIF to collections
#             which publish their datasets to GBIF.  BISON maintains this value 
#             in records they retrieve from GBIF. 
#             
#         TODO: Not yet implemented!
#         """
#         try:
#             usr_params = self._standardize_params(
#                 dataset_key=dataset_key, match_itis=match_itis, count_only=count_only)
#             namestr = usr_params['namestr']
#             if namestr is None:
#                 return self._show_online()
#             else:
#                 return self._get_records(dataset_key, usr_params['count_only'])
#         except Exception as e:
#             return self.get_failure(query_term=dataset_key, errors=[str(e)])

# .............................................................................
@cherrypy.expose
class DatasetTentacles(_DatasetSvc):
    PROVIDER = ServiceProvider.S2N
    # ...............................................
    def _get_records(self, dsid, count_only):
        allrecs = []
        
        # GBIF copy/s of Specify Record
        dg = DatasetGBIF()
        gbif_output = dg.GET(dataset_key=dsid, count_only=count_only)
        allrecs.append(gbif_output)

        full_out = S2nOutput(
            len(allrecs), dsid, APIService.Dataset, self.PROVIDER, 
            records=allrecs)        
        return full_out

    # ...............................................
    # ...............................................
    @cherrypy.tools.json_out()
    def GET(self, dataset_key=None, count_only=False, **kwargs):
        """Get one or more occurrence records for a dataset identifier from all
        available occurrence record services.
        
        Args:S2
            dataset_key: a unique dataset identifier for a collection of 
                occurrence records.
            count_only: flag to indicate whether to return only a count, or 
                a count and records
            kwargs: any additional keyword arguments are ignored

        Return:
            a dictionary with keys for each service queried.  Service values 
            LmRex.services.api.v1.S2nOutput object with optional records as a 
            list of dictionaries of GBIF records corresponding to specimen 
            occurrences in the GBIF database
              
        Note: 
            If count_only=False, the records element will contain a subset of 
            records available for that dataset.  The number of records will be
            less than or equal to the paging limit set by the provider.  
        Note: 
            The dataset_key is an identifier assigned by GBIF to collections
            which publish their datasets to GBIF.  BISON maintains this value 
            in records they retrieve from GBIF. 
        """
        try:
            usr_params = self._standardize_params(
                dataset_key=dataset_key, count_only=count_only)
            return self._get_records(
                usr_params['dataset_key'], usr_params['count_only'])
        except Exception as e:
            return self.get_failure(errors=[str(e)])

# .............................................................................
if __name__ == '__main__':
    # test
    from LmRex.common.lmconstants import TST_VALUES
    
    gocc = DatasetGBIF()
    for count_only in [True, False]:
        out = gocc.GET(
            TST_VALUES.DS_GUIDS_W_SPECIFY_ACCESS_RECS[0], count_only=count_only)
        print_s2n_output(out)
            

