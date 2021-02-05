

S-to-the-n services
----------------------

 * map: return metadata containing url endpoint for map and layernames for 
   predicted species distribution and occurrence points
 * name    
 * occ: <server>/api/v1/occ
 * dataset: <server>/api/v1/dataset 
 * resolve: <server>/api/v1/resolve/specify

* The core APIs are defined in the directory: src/LmRex/services/api/v1 .
  There are currently 5 files (categories) that organize them: 
    map, name, occ, dataset, resolve, and I will add a 6th - heartbeat. 
    
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
    PROVIDER in each subclass 
    
