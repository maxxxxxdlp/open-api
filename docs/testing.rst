
Testing T-Rex elements
----------------------

* On test VM, clone this repo, then symlink to 
  appropriate places on lmcore testing VM
  
  * make sure /opt/lifemapper/__init__.py exists
  * symlink t-rex/src dir to /opt/lifemapper/LmRex
  * symlink t-rex/solrcores/spcoco dirs to /var/solr/cores/

* Solr commands at /opt/solr/bin/ (in PATH)

    * Create new core::
      su -c "solr create -c spcoco -d /var/solr/cores/spcoco/conf -s 2 -rf 2" solr
    
    * Delete core::
      solr delete -c spcoco
      
    * Options to populate solr data into newly linked core::
      post -c spcoco t-rex/data/solrtest/*csv
      
    * Options to search: 
      
      * curl "http://localhost:8983/solr/spcoco/select?q=*.*"