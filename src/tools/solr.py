import requests
import subprocess

from LmRex.common.lmconstants import TST_VALUES
from LmRex.tools.api import APIQuery

SOLR_SERVER = '129.237.201.192'
SOLR_POST_COMMAND = '/opt/solr/bin/post'
SOLR_COMMAND = '/opt/solr/bin/solr'
CURL_COMMAND = '/usr/bin/curl'
ENCODING='utf-8'

"""
Defined solrcores in /var/solr/data/cores/
"""
# ......................................................
def count_docs(collection, solr_location=SOLR_SERVER):
    count, docs = query(collection, solr_location=solr_location)
    return count

# ...............................................
def _post_remote(collection, fname, solr_location=SOLR_SERVER, headers={}):
    response = output = retcode = None
    solr_endpt = 'http://{}:8983/solr'.format(solr_location)
    url = '{}/{}/update'.format(solr_endpt, collection)
    params = {'commit' : 'true'}
    with open(fname, 'r', encoding=ENCODING) as in_file:
        data = in_file.read()
        
    try:
        response = requests.post(url, data=data, params=params, headers=headers)
    except Exception as e:
        if response is not None:
            retcode = response.status_code
        else:
            print('Failed on URL {} ({})'.format(url, str(e)))
    else:
        if response.ok:
            retcode = response.status_code
            try:
                output = response.json()
            except Exception as e:
                try:
                    output = response.content
                except Exception:
                    output = response.text
                else:
                    print('Failed to interpret output of URL {} ({})'
                        .format(url, str(e)))
        else:
            try:
                retcode = response.status_code        
                reason = response.reason
            except:
                print('Failed to find failure reason for URL {} ({})'
                    .format(url, str(e)))
            else:
                print('Failed on URL {} ({}: {})'
                        .format(url, retcode, reason))
                print('Full response:')
                print(response.text)
    return retcode, output


# .............................................................................
def _post_local(collection, fname):
    """Post a document to a Solr index.
    
    Args:
        collection: name of the Solr collection to be posted to 
        fname: Full path the file containing data to be indexed in Solr
        solr_location: URL to solr instance (i.e. http://localhost:8983/solr)
    """
    cmd = '{} -c {} {} '.format(SOLR_POST_COMMAND, collection, fname)
    output, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return output

# .............................................................................
def post(collection, fname, solr_location=None, headers=None):
    """Post a document to a Solr index.
    
    Args:
        collection: name of the Solr collection to be posted to 
        fname: Full path the file containing data to be indexed in Solr
        solr_location: URL to solr instance (i.e. http://localhost:8983/solr)
    """
    retcode = 0
    if solr_location is not None:
        retcode, output = _post_remote(collection, fname, solr_location, headers)
    else:
        output = _post_local(collection, fname)
    return retcode, output

# .............................................................................
def query_guid(collection, guid, solr_location=SOLR_SERVER):
    """
    Query a Specify resolver index and return results for an occurrence in 
    JSON format.
    
    Args:
        collection: name of the Solr index
        guid: Unique identifier for record of interest
        solr_location: FQDN or IP of the Solr server
    
    Returns:
        Zero or one Solr records
    """
    doc = {}
    filters = {'id': guid}
    count, docs = query(collection, filters=filters, solr_location=solr_location)
    if count == 1: 
        doc = docs[0]
    return doc
    
# .............................................................................
def query(collection, filters={'*': '*'}, solr_location=SOLR_SERVER):
    """
    Query a solr index and return results in JSON format
    """
    count = 0 
    docs = {}
    solr_endpt = 'http://{}:8983/solr/{}/select'.format(solr_location, collection)
    api = APIQuery(solr_endpt, q_filters=filters)
    api.query_by_get(output_type='json')
    try:
        data = api.output['response']
    except:
        raise Exception('Failed to return response element')
    try:
        docs = data['docs']
    except:
        raise Exception('Failed to return docs')
    try:
        count = data['numFound']
    except:
        raise Exception('Failed to return docs')
    return count, docs

# .............................................................................
def update(collection, solr_location=SOLR_SERVER):
    url = '{}/{}/update'.format(solr_location, collection)
    cmd = '{} {}'.format(CURL_COMMAND, url)
    output, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return output

# .............................................................................
if __name__ == '__main__':
    # test
    TST_COLLECTION = 'spcoco'
    doc = count_docs(TST_COLLECTION)
    print('Found {} records in {}'.format(doc, TST_COLLECTION))
    for guid in TST_VALUES.BIRD_OCC_GUIDS:
        doc = query_guid(TST_COLLECTION, guid)
        print('Found {} record for guid {}'.format(doc, guid))

"""
Post:
/opt/solr/bin/post -c spcoco /state/partition1/git/t-rex/data/solrtest/occurrence.solr.csv

Query:
curl http://notyeti-192.lifemapper.org:8983/solr/spcoco/select?q=occurrence_guid:47d04f7e-73fa-4cc7-b50a-89eeefdcd162
curl http://notyeti-192.lifemapper.org:8983/solr/spcoco/select?q=*:*
"""
