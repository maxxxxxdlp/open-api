from LmRex.common.lmconstants import (
    APIService, Lifemapper, ServiceProvider, TST_VALUES)
from LmRex.fileop.logtools import (log_error)
from LmRex.services.api.v1.s2n_type import S2nKey, S2nOutput
from LmRex.tools.provider.api import APIQuery

# .............................................................................
class LifemapperAPI(APIQuery):
    """Class to query Lifemapper portal APIs and return results"""
    PROVIDER = ServiceProvider.Lifemapper['name']
    # ...............................................
    def __init__(
            self, resource=Lifemapper.PROJ_RESOURCE, ident=None, command=None,  
            other_filters={}, logger=None):
        """Constructor
        
        Args:
            resource: Lifemapper service to query
            ident: a Lifemapper database key for the specified resource.  If 
                ident is None, list using other_filters
            command: optional 'count' to query with other_filters
            other_filters: optional filters
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    
        """
        url = '{}/{}'.format(Lifemapper.URL, resource)
        if ident is not None:
            url = '{}/{}'.format(url, ident)
            # do not send filters if retrieving a known object
            other_filters = {}
        elif command in Lifemapper.COMMANDS:
            url = '{}/{}'.format(url, command)
        APIQuery.__init__(self, url, other_filters=other_filters, logger=logger)

    
    # ...............................................
    @classmethod
    def _standardize_map_record(cls, rec, color=None):
        try:
            mapname = rec['map']['mapName']
            url = rec['map']['endpoint']
        except Exception as e:
            msg = 'Failed to retrieve map url from {}, {}'.format(rec, e)
            raise Exception(msg)
        else:
            endpoint = '{}/{}'.format(url, mapname)
            try:
                data_url = rec['spatialRaster']['dataUrl']
            except:
                msg = 'Failed to get projection API link (spatialRaster/dataUrl)'
                raise Exception(msg)
            else:        
                proj_url = data_url.rstrip('/gtiff')
                try:
                    occid = rec['occurrenceSet']['id']
                    point_url = rec['occurrenceSet']['metadataUrl']
                    point_name = 'occ_{}'.format(occid)
                    newrec = {
                        'endpoint': endpoint,
                        'point_link': point_url,
                        'point_name': point_name,
                        'species_name': rec['speciesName'],
                        'modtime': rec['statusModTime'],
                        'projection_link': proj_url}
                except Exception as e:
                    msg = 'Failed to retrieve point data from {}, {}'.format(rec, e)
                    raise Exception(msg)
        
        # Ran the gauntlet of exceptions
        if color is not None:
            newrec['vendor-specific-parameters'] = {'color': color}
        # Minor errors return messages within record
        record_errors = []
        try:
            stat = rec['status']
        except:
            msg = 'Failed to get projection \'status\' for layer {}'.format(
                proj_url)
            record_errors.append(msg)
        else:
            # No projection layer without Complete status 
            if stat == Lifemapper.COMPLETE_STAT_VAL:
                try:
                    newrec['projection_name'] = rec['map']['layerName']
                except:
                    msg = 'Failed to get projection map/layerName from {}'.format(
                        proj_url)
                    record_errors.append(msg)
                # Add projection metadata
                try:
                    prj_metadata = rec['metadata']
                except:
                    msg = 'Failed to retrieve projection metadata for {}'.format(
                        proj_url)
                    record_errors.append(msg)
                for key in Lifemapper.PROJECTION_METADATA_KEYS:
                    try:
                        prj_metadata[key] = rec[key]
                    except:
                        msg = 'Failed to retrieve projection {} for {}'.format(
                            key, proj_url)
                        record_errors.append(msg)
        if len(record_errors) > 0:
            newrec[S2nKey.ERRORS] = record_errors
        return newrec
    
    # ...............................................
    @classmethod
    def _standardize_occ_record(cls, rec, color=None):
        errmsgs = []
        try:
            mapname = rec['map']['mapName']
            url = rec['map']['endpoint']
            point_name = rec['map']['layerName']
        except Exception as e:
            msg = 'Failed to retrieve map url from {}, {}'.format(rec, e)
            raise Exception(msg)
        else:
            endpoint = '{}/{}'.format(url, mapname)
            try:
                rec['spatialVector']
            except:
                errmsgs.append('Missing spatialVector element')
            else:
                bbox = ptcount = None
                try:
                    bbox = rec['spatialVector']['bbox']
                except:
                    errmsgs.append('Missing spatialVector/bbox element')
                try:
                    ptcount = rec['spatialVector']['numFeatures']
                except:
                    errmsgs.append('Missing spatialVector/numFeatures element')

                try:
                    occid = rec['id']
                    point_url = rec['url']
                    newrec = {
                        'endpoint': endpoint,
                        'point_link': point_url,
                        'point_name': point_name,
                        'point_count': ptcount,
                        'point_bbox': bbox,
                        'species_name': rec['speciesName'],
                        'modtime': rec['statusModTime']}
                except Exception as e:
                    msg = 'Failed to retrieve point data from {}, {}'.format(rec, e)
                    raise Exception(msg)
        
        try:
            stat = rec['status']
        except:
            errmsgs.append(cls._get_error_message(
                msg='Missing `status` element'))
        else:
            # No projection layer without Complete status 
            if stat != Lifemapper.COMPLETE_STAT_VAL:
                errmsgs.append(cls._get_error_message(
                    msg='Occurrenceset status is not complete'))
        newrec[S2nKey.ERRORS] = errmsgs
        return newrec

    # ...............................................
    @classmethod
    def _standardize_map_output(cls, output, color=None, count_only=False, err=None):
        stdrecs = []
        errmsgs = []
        total = len(output)
        if err is not None:
            errmsgs.append(err)
        # Records]
        if not count_only:
            for r in output:
                try:
                    stdrecs.append(cls._standardize_map_record(r, color=color))
                except Exception as e:
                    errmsgs.append(cls._get_error_message(err=e))
        
        # TODO: revisit record format for other map providers
        std_output = S2nOutput(
            count=total, record_format=Lifemapper.RECORD_FORMAT_MAP, 
            records=stdrecs, provider=cls.PROVIDER, errors=errmsgs, 
            provider_query=None, query_term=None, service=None)

        return std_output
    
    # ...............................................
    @classmethod
    def _standardize_occ_output(cls, output, color=None, count_only=False, err=None):
        stdrecs = []
        errmsgs = []
        total = len(output)
        if err is not None:
            errmsgs.append(err)
        # Records]
        if not count_only:
            for r in output:
                try:
                    stdrecs.append(cls._standardize_occ_record(r, color=color))
                except Exception as e:
                    errmsgs.append(cls._get_error_message(err=e))
        
        # TODO: revisit record format for other map providers
        std_output = S2nOutput(
            count=total, record_format=Lifemapper.RECORD_FORMAT_OCC, 
            records=stdrecs, provider=cls.PROVIDER, errors=errmsgs, 
            provider_query=None, query_term=None, service=None)

        return std_output
#     # ...............................................
#     @classmethod
#     def _construct_map_url(
#             cls, rec, bbox, color, exceptions, height, layers, frmat, request, 
#             srs, transparent, width):
#         """
#         service=wms&request=getmap&version=1.0&srs=epsg:4326&bbox=-180,-90,180,90&format=png&width=600&height=300&layers=prj_1848399
#         """
#         try:
#             mapname = rec['map']['mapName']
#             lyrname = rec['map']['layerName']
#             url = rec['map']['endpoint']
#         except Exception as e:
#             msg = 'Failed to retrieve map data from {}, {}'.format(rec, e)
#             rec = {'spcoco.error': msg}
#         else:
#             tmp = layers.split(',')
#             lyrcodes = [t.strip() for t in tmp]
#             lyrnames = []
#             # construct layers for display from bottom layer up to top: 
#             #     bmng (background image), prj (projection), occ (points)
#             if 'bmng' in lyrcodes:
#                 lyrnames.append('bmng')
#             if 'prj' in lyrcodes:
#                 lyrnames.append(lyrname)
#             if 'occ' in lyrcodes:
#                 try:
#                     occid = rec['occurrenceSet']['id']
#                 except:
#                     msg = 'Failed to retrieve occurrence layername'
#                 else:
#                     occlyrname = 'occ_{}'.format(occid)
#                     lyrnames.append(occlyrname)
#             lyrstr = ','.join(lyrnames)
#             
#             filters = {
#                 'bbox': bbox, 'height': height, 'layers': lyrstr, 
#                 'format': frmat, 'request': request, 'srs': srs, 'width': width}
#             # Optional, LM-specific, filters
#             # TODO: fix color parameter in Lifemapper maps
# #             if color is not None:
# #                 filters['color'] = color 
#             if exceptions is not None:
#                 filters['exceptions'] = exceptions
#             if transparent is not None:
#                 filters['transparent'] = transparent
#                 
#             filter_str = 'service=wms&version=1.0'
#             for (key, val) in filters.items():
#                 filter_str = '{}&{}={}'.format(filter_str, key, val) 
#             map_url = '{}/{}?{}'.format(url, mapname, filter_str)
#         return map_url
# 
#     # ...............................................
#     @classmethod
#     def find_projections_by_name(
#             cls, name, prjscenariocode=None, bbox='-180,-90,180,90', 
#             color=None, exceptions=None, height=300, layers='prj', frmat='png', 
#             request='getmap', srs='epsg:4326',  transparent=None, width=600, 
#             other_filters={}, logger=None):
#         """
#         List projections for a given scientific name.  
#         
#         Args:
#             name: a scientific name 'Accepted' according to the GBIF Backbone 
#                 Taxonomy
#             prjscenariocode: a Lifemapper code indicating whether the 
#                 environmental data used for creating the projection is 
#                 observed, or modeled past or future.  Codes are in 
#                 LmREx.common.lmconstants Lifemapper.*_SCENARIO_CODE*. If the 
#                 code is None, return a map with only occurrence points
#             logger: optional logger for info and error messages.  If None, 
#                 prints to stdout    
# 
#         Note: 
#             Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
#             Taxonomy and this method requires them for success.
# 
#         Todo:
#             handle full record returns instead of atoms
#         """
#         output = {}
#         recs = []
#         other_filters[Lifemapper.NAME_KEY] = name
#         other_filters[Lifemapper.ATOM_KEY] = 0
# #         other_filters[Lifemapper.MIN_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
# #         other_filters[Lifemapper.MAX_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
#         if prjscenariocode is not None:
#             other_filters[Lifemapper.SCENARIO_KEY] = prjscenariocode
#         api = LifemapperAPI(
#             resource=Lifemapper.PROJ_RESOURCE, other_filters=other_filters)
#         try:
#             api.query_by_get()
#         except Exception:
#             msg = 'Failed on {}'.format(api.url)
#             log_error(msg, logger=logger)
#             output[S2nKey.ERRORS_KEY] = msg
#         else:
#             # output returns a list of records
#             recs = api.output
#             if len(recs) == 0:
#                 output['warning'] = 'Failed to find projections for {}'.format(
#                     name)
#             background_layer_name = 'bmng'
#             for rec in recs:
#                 # Add base WMS map url with LM-specific parameters into 
#                 #     map section of metadata
#                 try:
#                     rec['map']['lmMapEndpoint'] = '{}/{}?layers={}'.format(
#                         rec['map']['endpoint'], rec['map']['mapName'],
#                         rec['map']['layerName'])
#                 except Exception as err:
#                     msg = 'Failed getting map url components {}'.format(err)
#                     log_error(msg, logger=logger)
#                     output[S2nKey.ERRORS_KEY] = msg
#                 else:
#                     # Add background layername into map section of metadata
#                     rec['map']['backgroundLayerName']  = background_layer_name
#                     # Add point layername into map section of metadata
#                     try:
#                         occ_layer_name = 'occ_{}'.format(rec['occurrenceSet']['id'])
#                     except:
#                         occ_layer_name = ''
#                     rec['map']['pointLayerName']  = occ_layer_name
#                     # Add full WMS map url with all required parameters into metadata
#                     url = LifemapperAPI._construct_map_url(
#                         rec, bbox, color, exceptions, height, layers, frmat, 
#                         request, srs, transparent, width)
#                     if url is not None:
#                         rec['map_url'] = url
#         output[S2nKey.COUNT_KEY] = len(recs)
#         output[S2nKey.RECORDS_KEY] = recs
#         return output

    # ...............................................
    @classmethod
    def find_map_layers_by_name(
            cls, name, prjscenariocode=None, color=None, other_filters={}, 
            logger=None):
        """
        List projections for a given scientific name.  
        
        Args:
            name: a scientific name 'Accepted' according to the GBIF Backbone 
                Taxonomy
            prjscenariocode: a Lifemapper code indicating whether the 
                environmental data used for creating the projection is 
                observed, or modeled past or future.  Codes are in 
                LmREx.common.lmconstants Lifemapper.*_SCENARIO_CODE*. If the 
                code is None, return a map with only occurrence points
            color: a string indicating a valid color for displaying a predicted
                distribution map 
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Note: 
            Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
            Taxonomy and this method requires them for success.

        Todo:
            handle full record returns instead of atoms
        """
        other_filters[Lifemapper.NAME_KEY] = name
        other_filters[Lifemapper.ATOM_KEY] = 0
#         other_filters[Lifemapper.MIN_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
#         other_filters[Lifemapper.MAX_STAT_KEY] = Lifemapper.COMPLETE_STAT_VAL
        if prjscenariocode is not None:
            other_filters[Lifemapper.SCENARIO_KEY] = prjscenariocode
        api = LifemapperAPI(
            resource=Lifemapper.PROJ_RESOURCE, other_filters=other_filters)
        
        try:
            api.query_by_get()
        except Exception as e:
            out = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            out = cls._standardize_map_output(
                api.output, color=color, count_only=False, err=api.error)

        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[api.url], query_term=name, 
            service=APIService.Dataset)
        return full_out

    # ...............................................
    @classmethod
    def find_occurrencesets_by_name(cls, name, logger=None):
        """
        List occurrences for a given scientific name.  
        
        Args:
            name: a scientific name 'Accepted' according to the GBIF Backbone 
                Taxonomy
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Note: 
            Lifemapper contains only 'Accepted' name froms the GBIF Backbone 
            Taxonomy and this method requires them for success.
        """
        api = LifemapperAPI(
            resource=Lifemapper.OCC_RESOURCE, 
            q_filters={Lifemapper.NAME_KEY: name})
        try:
            api.query_by_get()
        except Exception as e:
            out = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_occ_output(api.output, err=api.error)

        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            query_term=name)
        return full_out    

    # ...............................................
    @classmethod
    def _get_occurrenceset_data(cls, url, logger=None):
        """
        Return occurrenceset for a given metadata url.  
        
        Args:
            url: a link to the metadata for a Lifemapper occurrenceSet
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    
        """
        api = APIQuery(url, logger=logger)
        try:
            api.query_by_get()
        except Exception as e:
            out = cls.get_failure(errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_occ_output(api.output, err=api.error)

        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[url])
        return full_out    


"""
http://client.lifemapper.org/api/v2/sdmproject?displayname=Conibiosoma%20elongatum&projectionscenariocode=worldclim-curr
http://client.lifemapper.org/api/v2/occurrence?displayname=Conibiosoma%20elongatum
"""
