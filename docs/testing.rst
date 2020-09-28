
Testing T-Rex elements
----------------------

* On test VM, clone this repo, then symlink to 
  appropriate places on lmcore testing VM
  
  * make sure /opt/lifemapper/__init__.py exists
  * symlink t-rex/src dir to /opt/lifemapper/LmRex
  * symlink t-rex/solrcores/* dirs to /share/lm/solr/cores/*

* Options to populate solr data into newly linked core:

  * /opt/solr/bin/solr -c spcoco t-rex/data/solrtest/*json
  
  
  
* Options to search: 
  
  * curl "http://localhost:8983/solr/spcoco/select?q=*.*"