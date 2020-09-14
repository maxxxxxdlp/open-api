import requests

SOLR_RESOLVER_COLLECTION = 'spcoco'
SOLR_POST_COMMAND = '/opt/solr/bin/post'
SOLR_SERVER = 'http://localhost:8983/solr/'
ENCODING='utf-8'

update_url = '{}/{}/update'.format(SOLR_SERVER, SOLR_RESOLVER_COLLECTION)

cmd = '{} -c {} '.

"""
Copy solr cores to /share/lm/solr/data/cores/

"""
# .............................................................................
def _post(collection, doc_filename, headers=None):
    """Post a document to a Solr index."""
    if not headers:
        headers = {}
    url = '{}{}/update?commit=true'.format(SOLR_SERVER, collection)

    with open(doc_filename, 'rb', encoding=ENCODING) as in_file:
        data_bytes= in_file.read()
    # urllib requires byte data for post
    req = urllib.request.Request(url, data=data_bytes, headers=headers)
    return urllib.request.urlopen(req).read()
format(SOLR_POST_COMMAND, SOLR_RESOLVER_COLLECTION)