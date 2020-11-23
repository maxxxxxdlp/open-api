
Specify GUID endpoints
----------------------

Specify7 server with single record export endpoint::
  http://preview.specifycloud.org/

to get one record::
  curl http://preview.specifycloud.org/export/record/56caf05f-1364-4f24-85f6-0c82520c2792/98fb49e0-591b-469e-99af-117b0bfdd7ee/ \
  | python -m json.tool
  
Browse with testlogin

Datasets and their IDs are listed in:: 
  http://preview.specifycloud.org/export/rss/
  
also IPT datasets::
  https://ichthyology.specify.ku.edu/export/rss/