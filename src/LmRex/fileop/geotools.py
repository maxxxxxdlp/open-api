import glob
import os
from osgeo import ogr, osr
import rtree

EXTRA_VALS_KEY = 'rest'
# Rough log of processing progress
LOGINTERVAL = 1000000
LOG_FORMAT = ' '.join(["%(asctime)s",
                       "%(funcName)s",
                       "line",
                       "%(lineno)d",
                       "%(levelname)-8s",
                       "%(message)s"])
LOG_DATE_FORMAT = '%d %b %Y %H:%M'
LOGFILE_MAX_BYTES = 52000000 
LOGFILE_BACKUP_COUNT = 5

REQUIRED_FIELDS = []
CENTROID_FIELD = 'CENTROID'

# .............................
def delete_shapefile(shp_filename):
    success = True
    shape_extensions = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.fbn',
                        '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx',
                        '.shp.xml', '.cpg', '.qix']
    if (shp_filename is not None 
        and os.path.exists(shp_filename) and shp_filename.endswith('.shp')):
        base, _ = os.path.splitext(shp_filename)
        similar_file_names = glob.glob(base + '.*')
        try:
            for simfname in similar_file_names:
                _, simext = os.path.splitext(simfname)
                if simext in shape_extensions:
                    os.remove(simfname)
        except Exception as err:
            success = False
            print('Failed to remove {}, {}'.format(simfname, str(err)))
    return success

# .............................................................................
def _create_empty_dataset(out_shp_filename, feature_attributes, ogr_type, 
                          epsg_code, overwrite=True):
    """ Create an empty ogr dataset given a set of feature attributes
    
    Args:
        out_shp_filename: filename for output data
        feature_attributes: an ordered list of feature_attributes.  
            Each feature_attribute is a tuple of (field name, field type (OGR))
        ogr_type: OGR constant indicating the type of geometry for the dataset
        epsg_code: EPSG code of the spatial reference system (SRS)
        overwrite: boolean indicating if pre-existing data should be deleted.
    
    """
    success = False
    if overwrite:
        delete_shapefile(out_shp_filename)
    elif os.path.isfile(out_shp_filename):
        print(('Dataset exists: {}'.format(out_shp_filename)))
        return success
    
    try:
        # Create the file object, a layer, and attributes
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(epsg_code)
        drv = ogr.GetDriverByName('ESRI Shapefile')

        dataset = drv.CreateDataSource(out_shp_filename)
        if dataset is None:
            raise Exception(
                'Dataset creation failed for {}'.format(out_shp_filename))

        lyr = dataset.CreateLayer(
            dataset.GetName(), geom_type=ogr_type, srs=target_srs)
        if lyr is None:
            raise Exception(
                'Layer creation failed for {}.'.format(out_shp_filename))

        # Define the fields
        for (fldname, fldtype) in feature_attributes:
            fld_defn = ogr.FieldDefn(fldname, fldtype)
            # Special case to handle long names
            if (fldname.endswith('name') and fldtype == ogr.OFTString):
                fld_defn.SetWidth(255)
            return_val = lyr.CreateField(fld_defn)
            if return_val != 0:
                raise Exception(
                    'CreateField failed for {} in {}'.format(
                        fldname, out_shp_filename))
        print('Created empty dataset with {} fields'.format(
            len(feature_attributes)))            
    except Exception as e:
        print('Failed to create shapefile {}'.format(out_shp_filename), e)
                    
    return dataset, lyr

# .............................................................................
def get_clustered_spatial_index(shp_filename):
    pth, basename = os.path.split(shp_filename)
    idxname, _ = os.path.splitext(basename)
    idx_filename = os.path.join(pth, idxname)

    if not(os.path.exists(idx_filename+'.dat')):
        # Create spatial index
        prop = rtree.index.Property()
        prop.set_filename(idx_filename)
        
        driver = ogr.GetDriverByName("ESRI Shapefile")
        datasrc = driver.Open(shp_filename, 0)
        lyr = datasrc.GetLayer()
        spindex = rtree.index.Index(idx_filename, interleaved=False, properties=prop)
        for fid in range(0, lyr.GetFeatureCount()):
            feat = lyr.GetFeature(fid)
            geom = feat.geometry()
            wkt = geom.ExportToWkt()
            # OGR returns xmin, xmax, ymin, ymax
            xmin, xmax, ymin, ymax = geom.GetEnvelope()
            # Rtree takes xmin, xmax, ymin, ymax IFF interleaved = False
            spindex.insert(fid, (xmin, xmax, ymin, ymax), obj=wkt)
        # Write spatial index
        spindex.close()
    else:
        spindex = rtree.index.Index(idx_filename, interleaved=False)
    return spindex

# .............................................................................
def _refine_intersect(gc_wkt, poly, new_layer, feat_vals):
    newfeat_count = 0
    # select only the intersections
    gridcell = ogr.CreateGeometryFromWkt(gc_wkt)
    if poly.Intersects(gridcell):
        intersection = poly.Intersection(gridcell)
        itxname = intersection.GetGeometryName()
        
        # Split polygon/gridcell intersection into 1 or more simple polygons
        itx_polys = []
        if itxname == 'POLYGON':
            itx_polys.append(intersection)
        elif itxname in ('MULTIPOLYGON', 'GEOMETRYCOLLECTION'):
            for i in range(intersection.GetGeometryCount()):
                subgeom = intersection.GetGeometryRef(i)
                subname = subgeom.GetGeometryName()
                if subname == 'POLYGON':
                    itx_polys.append(subgeom)
                else:
                    print('{} intersection subgeom, simple {}, count {}'.format(
                        subname, subgeom.IsSimple(), subgeom.GetGeometryCount()))
        else:
            print('{} intersection geom, simple {}, count {}'.format(
                itxname, intersection.IsSimple(), intersection.GetGeometryCount()))

        # Make a feature from each simple polygon
        for ipoly in itx_polys:
            try:
                newfeat = ogr.Feature(new_layer.GetLayerDefn())
                # Makes a copy of the ipoly for the new feature
                newfeat.SetGeometry(ipoly)
                # put values into fieldnames
                for fldname, fldval in feat_vals.items():
                    if fldname != 'geometries' and fldval is not None:
                        newfeat.SetField(fldname, fldval)
            except Exception as e:
                print('      Failed to fill feature, e = {}'.format(e))
            else:
                # Create new feature, setting FID, in this layer
                new_layer.CreateFeature(newfeat)
                newfeat.Destroy()
                newfeat_count += 1
    return newfeat_count

# .............................................................................
def intersect_write_shapefile(new_dataset, new_layer, feats, grid_index):
    feat_count = 0
    # for each feature
    print ('Loop through {} poly features for intersection'.format(len(feats)))
    for fid, feat_vals in feats.items():
        curr_count = 0
        # create new feature for every simple geometry
        simple_wkts = feat_vals['geometries']
        print ('  Loop through {} simple features in poly'.format(
            len(simple_wkts)))
        for wkt in simple_wkts:
            # create a new feature
            simple_geom = ogr.CreateGeometryFromWkt(wkt)
            gname = simple_geom.GetGeometryName()
            if gname != 'POLYGON':
                print ('    Discard invalid {} subgeometry'.format(gname))
            else:
                # xmin, xmax, ymin, ymax
                xmin, xmax, ymin, ymax = simple_geom.GetEnvelope()
                hits = list(grid_index.intersection((xmin, xmax, ymin, ymax), 
                                                    objects=True))
                print ('    Loop through {} roughly intersected gridcells'.format(len(hits)))
                for item in hits:
                    gc_wkt = item.object
                    newfeat_count = _refine_intersect(
                        gc_wkt, simple_geom, new_layer, feat_vals)
                    curr_count += newfeat_count
#                     print ('  Created {} new features for simplified poly'.format(
#                         newfeat_count))
        print ('  Created {} new features for primary poly'.format(curr_count))
        feat_count += curr_count
    print ('Created {} new features from intersection'.format(feat_count))
    # Close and flush to disk
    new_dataset.Destroy()

# .............................................................................
def write_shapefile(new_dataset, new_layer, feature_sets, calc_nongeo_fields):
    """ Write a shapefile given a set of features, attribute
    
    Args:
        new_dataset: an OGR dataset object for the new shapefile
        new_layer: an OGR layer object with feature
        newfield_mapping = 
    """
    feat_count = 0
    new_layer_def = new_layer.GetLayerDefn()
    # for each set of features
    for feats in feature_sets:
        # for each feature
        for oldfid, feat_vals in feats.items():
            # create new feature for every simple geometry
            simple_geoms = feat_vals['geometries']
            for wkt in simple_geoms:
                try:
                    # create a new feature
                    newfeat = ogr.Feature(new_layer_def)
                    poly = ogr.CreateGeometryFromWkt(wkt)
                    # New geom can be assigned directly to new feature
                    newfeat.SetGeometryDirectly(poly)
                    # put old dataset values into old fieldnames
                    for fldname, fldval in feat_vals.items():
                        if fldname != 'geometries' and fldval is not None:
                            newfeat.SetField(fldname, fldval)
                except Exception as e:
                    print('Failed to fill feature, e = {}'.format(e))
                else:
                    # Create new feature, setting FID, in this layer
                    new_layer.CreateFeature(newfeat)
                    newfeat.Destroy()
                    feat_count += 1
        print('Wrote {} records from feature set'.format(feat_count))
        feat_count = 0

    # Close and flush to disk
    new_dataset.Destroy()


# .............................................................................
def _read_complex_shapefile(in_shp_filename):
    ogr.RegisterAll()
    drv = ogr.GetDriverByName('ESRI Shapefile')
    try:
        dataset = drv.Open(in_shp_filename)
    except Exception:
        print('Unable to open {}'.format(in_shp_filename))
        raise

    try:
        lyr = dataset.GetLayer(0)
    except Exception:
        print('Unable to get layer from {}'.format(in_shp_filename))
        raise 

    (min_x, max_x, min_y, max_y) = lyr.GetExtent()
    bbox = (min_x, min_y, max_x, max_y)
    lyr_def = lyr.GetLayerDefn()
    fld_count = lyr_def.GetFieldCount()

    # Read Fields (indexes start at 0)
    feat_attrs = []
    for i in range(fld_count):
        fld = lyr_def.GetFieldDefn(i)
        fldname = fld.GetNameRef()
        fldtype = fld.GetType()
        # ignore these fields
        if fldname not in ('JSON', 'EXTENT', 'ALAND', 'AWATER', 'Area_m2'):
            if fldname == 'MRGID':
                fldtype = ogr.OFTInteger
            feat_attrs.append((fldname, fldtype))
    
    # Read Features
    feats = {}
    try:
        old_feat_count = lyr.GetFeatureCount()
        new_feat_count = 0
        for fid in range(0, lyr.GetFeatureCount()):
            feat = lyr.GetFeature(fid)
            feat_vals = {}
            for (fldname, _) in feat_attrs:
                try:
                    val = feat.GetFieldAsString(fldname)
                except:
                    val = ''
                    if fldname in REQUIRED_FIELDS:
                        print('Failed to read value in {}, FID {}'.format(
                            fldname, fid))
                feat_vals[fldname] = val
            # Save centroid of original polygon
            geom = feat.geometry()
            geom_name = geom.GetGeometryName()
            centroid = geom.Centroid()
            feat_vals[CENTROID_FIELD] = centroid.ExportToWkt() 
            # Split multipolygon into 1 record - 1 simple polygon
            feat_wkts = []
            if geom_name == 'POLYGON':
                feat_wkts.append(geom.ExportToWkt())
            elif geom_name in ('MULTIPOLYGON', 'GEOMETRYCOLLECTION'):
                for i in range(geom.GetGeometryCount()):
                    subgeom = geom.GetGeometryRef(i)
                    subname = subgeom.GetGeometryName()
                    if subname == 'POLYGON':
                        feat_wkts.append(subgeom.ExportToWkt())
                    else:
                        print('{} subgeom, simple {}, count {}'.format(
                            subname, subgeom.IsSimple(), subgeom.GetGeometryCount()))
            else:
                print('{} primary geom, simple {}, count {}'.format(
                    geom_name, geom.IsSimple(), geom.GetGeometryCount()))
            # Add one or more geometries to feature
            if len(feat_wkts) == 0:
                feat_wkts.append(geom.ExportToWkt())
            feat_vals['geometries'] = feat_wkts
            new_feat_count += len(feat_wkts)
            feats[fid] = feat_vals
        print('Read {} features into {} simple features'.format(
            old_feat_count, new_feat_count))

    except Exception as e:
        raise Exception('Failed to read features from {} ({})'.format(
            in_shp_filename, e))
        
    finally:
        lyr = None
        dataset = None
        
    return feats, feat_attrs, bbox

# .............................................................................
def simplify_merge_polygon_shapefiles(in_shp_filenames, calc_fields, out_shp_filename):
    ''' Merge one or more shapefiles, simplifying multipolygons into simple polygons with
    the same attribute values.
    
    Args:
        in_shp_filenames: list of one or more input shapefiles 
        newfield_mapping: dictionary of new fields, fieldtypes
        out_shp_filename: output filename
    '''
    epsg_code = 4326
    # Open input shapefiles, read layer def
    features_lst = []
    feat_attrs_lst = []
    bboxes = []
    for shp_fname in in_shp_filenames:
        # Calculate B_CENTROID and save values of original polygon/feature
        feats, feat_attrs, bbox = _read_complex_shapefile(shp_fname)
        features_lst.append(feats)
        feat_attrs_lst.append(feat_attrs)
        bboxes.append(bbox)

    # ......................... Merge attributes .........................
    out_feat_attrs = []
    new_fldnames = []
    for i in range(len(feat_attrs_lst)):
        feat_attrs = feat_attrs_lst[i]
        for (fname,ftype) in feat_attrs:
            if fname in new_fldnames:
                fname = fname + str(i)
            new_fldnames.append(fname)
            out_feat_attrs.append((fname,ftype))
    # Add new attributes including B_CENTROID
    for calc_fldname, calc_fldtype in calc_fields.items():
        out_feat_attrs.append((calc_fldname, calc_fldtype))
        new_fldnames.append(calc_fldname)

    # ......................... ? bbox .........................
    new_bbox = (min([b[0] for b in bboxes]), min([b[1] for b in bboxes]),
                max([b[2] for b in bboxes]), max([b[3] for b in bboxes]))
        
    # ......................... Create structure .........................
    out_dataset, out_layer = _create_empty_dataset(
        out_shp_filename, out_feat_attrs, ogr.wkbPolygon, epsg_code, 
        overwrite=True)
    
    # ......................... Write old feats to new layer  .........................
    # Calculate non-geometric fields
    # Write one or more new features for each original feature
    calc_nongeo_fields = [k for k in calc_fields.keys() if k != CENTROID_FIELD] 
    write_shapefile(
        out_dataset, out_layer, features_lst, calc_nongeo_fields)


# .............................................................................
def intersect_polygon_with_grid(primary_shp_filename, grid_shp_filename, 
                                calc_fields, out_shp_filename):
    ''' Intersect a primary shapefile with a grid (or other simple polygon) 
    shapefile, simplifying multipolygons in the primary shapefile into simple 
    polygons. Intersect the simple polygons with gridcells in the second 
    shapefile to further reduce polygon size and complexity.
    
    Args:
        in_shp_filenames: list of one or more input shapefiles 
        grid_shp_filename: dictionary of new fields, fieldtypes
        out_shp_filename: output filename
    '''
    epsg_code = 4326
    # Open input shapefile, read layer def
    feats, feat_attrs, bbox = _read_complex_shapefile(primary_shp_filename)
    
    # Add new attributes including B_CENTROID
    for calc_fldname, calc_fldtype in calc_fields.items():
        feat_attrs.append((calc_fldname, calc_fldtype))
         
    # Get spatial index for grid with WKT for each cell
    grid_index = get_clustered_spatial_index(grid_shp_filename)
 
    # ......................... Create structure .........................
    out_dataset, out_layer = _create_empty_dataset(
        out_shp_filename, feat_attrs, ogr.wkbPolygon, epsg_code, 
        overwrite=True)
       
    # ......................... Intersect polygons .........................
    intersect_write_shapefile(out_dataset, out_layer, feats, grid_index)
        

# ...............................................
if __name__ == '__main__':
    pth = '/tank/data/bison/2019/ancillary'    
    # Marine boundaries
    eez_orig_sfname = 'World_EEZ_v8_20140228_splitpolygons/World_EEZ_v8_2014_HR.shp'
    grid_sfname = 'world_grid_2.5.shp'
    # Same as ANCILLARY_FILES['marine']['file']
    eez_outfname = 'eez_gridded_boundaries_2.5.shp'
    orig_eez_filename = os.path.join(pth, eez_orig_sfname)
    grid_shp_filename = os.path.join(pth, grid_sfname)
    intersect_filename = os.path.join(pth, eez_outfname)
    calc_eez_fields = {CENTROID_FIELD: ogr.OFTString}
    intersect_polygon_with_grid(orig_eez_filename, grid_shp_filename, 
                                calc_eez_fields, intersect_filename)
    
"""

"""