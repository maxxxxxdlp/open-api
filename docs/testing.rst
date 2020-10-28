
Testing T-Rex elements
----------------------

* On test VM, clone this repo, then symlink to 
  appropriate places on lmcore testing VM
  
  * make sure /opt/lifemapper/__init__.py exists
  * symlink t-rex/src dir to /opt/lifemapper/LmRex  
    su -c "ln -s /state/partition1/git/t-rex/solrcores/spcoco /var/solr/cores/
  * symlink (as solr user) t-rex/solrcores/spcoco dirs to /var/solr/cores/

* Solr commands at /opt/solr/bin/ (in PATH)

    * Create new core::
      su -c "/opt/solr/bin/solr create -c spcoco -d /var/solr/cores/spcoco/conf -s 2 -rf 2" solr
    
    * Delete core::
      /opt/solr/bin/solr delete -c spcoco
      
    * Options to populate solr data into newly linked core::
      * /opt/solr/bin/post -c spcoco t-rex/data/solrtest/*csv
      * curl -c spcoco t-rex/data/solrtest/*csv
      
    * Options to search: 
      
      * curl "http://localhost:8983/solr/spcoco/select?q=*.*"