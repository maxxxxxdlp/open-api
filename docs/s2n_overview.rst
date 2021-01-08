

S-to-the-n services
----------------------
 * map 

   * parameters: namestr, [optional listed below for specific map boundaries, etc]
   * provider Lifemapper: <server>/api/v1/map/lm
 
 * name 
 
   * parameters: namestr 
     [GBIF and Tentacles: gbif_accepted(default True), gbif_count(default True)]
   * Tentacles: <server>/api/v1/name
   * GBIF: <server>/api/v1/name/gbif
   * ITIS: <server>/api/v1/name/itis
   
 * occ Tentacles: : <server>/api/v1/occ
 
   * parameters: occurrenceid, count_only (default False)
   * Tentacles: <server>/api/v1/name
   * GBIF: <server>/api/v1/name/gbif
   * ITIS: <server>/api/v1/name/itis
 
 * dataset Tentacles: : <server>/api/v1/dataset
 
   * parameters: datasetid, count_only (default True)
   * Tentacles: <server>/api/v1/dataset
   * GBIF: <server>/api/v1/name/gbif
   * BISON: <server>/api/v1/name/bison
 
 * resolve Specify: <server>/api/v1/resolve/specify
 
   * parameters: occurrenceid (Specify GUID)

 , occ, resolve
* The core APIs are defined in the directory: src/LmRex/services/api/v1 .
  There are currently 4 files (categories) that organize them: 
    map, name, occ, resolve, and I will add a 5th - heartbeat. 
    
* There is another category/service: dataset, which is contained in the occ.py 
  file and returns or counts occurrence records by some filter (currently only 
  dataset key).  This will return data synchronously, but will change to pull
  records asynchronously, and only return a count synchronously.

* The classes in these files all inherit from _S2nService in the base.py file, 
  which implements some methods to ensure they all behave consistently and use a 
  subset of the same parameters and defaults.  The _standardize_params method 
  contains defaults for url keyword parameters.

  The root.py file contains the cherrypy commands and configuration to expose 
  the services.

In the src/LmRex/common/lmconstants.py file are the constants that are used in 
multiple places. 

  * **TST_VALUES** contains names and guids that can be used for testing
    services, some will return data, some will not, but none should return 
    errors.
  * **APIService** contains the URL service endpoints for the different 
    categories of services. 
  * **ServiceProvider** contains the name, endpoint, and service categories 
    available for that provider.
  * All service endpoints (following the server url) will start the 
    root (/api/v1), then category.  The "tentacles" service that queries all 
    available providers for that category will be at that endpoint 
    (example: /api/v1/name).  The endpoint for each individual provider will be 
    appended to the url for a single provider query 
    (example: /api/v1/occ/gbif uses ServiceProvider.GBIF['endpoint']).  
  * These URL endpoints are constructed in the base class classmethod  
    _S2nService.endpoint() using the class attributes SERVICE_PROVIDER and 
    PROVIDER in each subclass (example:  lines 12 and 17 of 
    src/LmRex/services/api/v1/occ.py)

Available services 
------------------
* Map services: return metadata containing url endpoint for map and 
  site-specific required parameters and full URL with site-specific and other
  WMS parameters.
  
  * providers:
  
    * Lifemapper: <server>/api/v1/map/lm

  * keyword parameters with default or valid options:
  
    * namestr:
      * taxon name for query
      * default None
      
    * scenariocode: 

      * code for observed, predicted past, predicted future climate data 
        used for predicting species distribution
      * valid options: worldclim-curr (default, observed climate)
        CMIP5-CCSM4-lgm-10min,  CMIP5-CCSM4-mid-10min (past climate)
        AR5-CCSM4-RCP8.5-2050-10min, AR5-CCSM4-RCP4.5-2050-10min, 
        AR5-CCSM4-RCP4.5-2070-10min, AR5-CCSM4-RCP8.5-2070-10min(future climate)

    * bbox:
    
      * coordinates for returned map, format minX,minY,maxX,maxY 
      * default: -180,-90,180,90
       
    * color: (currently ignored)
    
      * color for predicted distribution of species
      * valid options: red (default), gray, green, blue, safe, pretty, yellow, 
        fuschia, aqua, bluered, bluegreen, greenred
       
    * height:
    
      * height in pixels for map 
      * default: 300
      
    * layers (Lifemapper map service only):
     
      * codes for map layers requested
      * valid options: prj (predicted distribution), occ (points from GBIF used '
        for predicted distribution), bmng (NASA Blue Marble Next Generation)
        
    * frmat 
    
      * image format for returned map
      * valid options: png (default), gif, jpeg
      
    * request
    
      * image format for returned map
      * valid options: png (default), gif, jpeg
      
    * srs 
    
      * spatial reference system for returned map
      * valid options: epsg:4326 (default), epsg:3857 (web mercator)
      
    * transparent 
    
      * flag indicating whether background of map image should be transparent 
        (allows layering onto other maps)
      * default: True
      
    * width 
    
      * width in pixels for returned map
      * default: 600
      
    * do_match
    
      * flag indicating whether to first match namestr to accepted taxon in GBIF
      * default: True
      
  * providers:
  
    * Lifemapper: /api/v1/map/lm
  
* Name services:

  * keyword parameters with default or valid options:
  
    * namestr: scientific name
    * gbif_parse: flag indicating whether to parse the scientific name (removing
      author and date information) (use for all providers)
    * gbif_accepted: flag indicating whether to limit results to 'accepted' taxa
      in GBIF Backbone Taxonomy (GBIF only)
    * gbif_count: flag indicating whether to return the number of occurrence
      points in GBIF for this taxon(GBIF only)

  * aggregated services: <server>/api/v1/name
  * providers:
  
    * GBIF: <server>/api/v1/name/gbif
    * ITIS: <server>/api/v1/name/itis

* Occurrence services:

  * keyword parameters with default or valid options:
  
    * occid: DWC:occurrenceid for a record
    * count_only: flag indicating whether to return the record(s) or only count
      default False

  * aggregated services: <server>/api/v1/occ
  * providers:
  
    * GBIF: <server>/api/v1/name/gbif
    * iDigBio: <server>/api/v1/name/idb
    * MorphoSource: <server>/api/v1/name/mopho
    * Specify: <server>/api/v1/name/specify


* Dataset (occurrence) services:

  * keyword parameters with default or valid options:
  
    * datasetid: datasetid for a record (GBIF UUID dataset_key)
    * count_only: flag indicating whether to return the record(s) or only count
      default False


  * aggregated services: not yet implemented 
  * providers:
  
    * GBIF: <server>/api/v1/dataset/gbif
    * BISON: not yet implemented

* Resolution services

  * aggregated services: not yet implemented 
  * providers:
  
    * Specify: <server>/api/v1/resolve/specify

