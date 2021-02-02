import requests
import subprocess

from LmRex.common.lmconstants import SPECIFY, TST_VALUES
from LmRex.tools.provider.api import APIQuery
from LmRex.services.api.v1.s2n_type import S2nKey        

SOLR_POST_COMMAND = '/opt/solr/bin/post'
SOLR_COMMAND = '/opt/solr/bin/solr'
CURL_COMMAND = '/usr/bin/curl'
ENCODING='utf-8'

"""
Defined solrcores in /var/solr/data/cores/
"""
# ......................................................
def count_docs(collection, solr_location):
    output = query(collection, solr_location)
    output.pop(S2nKey.RECORDS)
    return output

# ...............................................
def _post_remote(collection, fname, solr_location, headers={}):
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
def _post_local(fname, collection):
    """Post a document to a Solr index.
    
    Args:
        fname: Full path the file containing data to be indexed in Solr
        collection: name of the Solr collection to be posted to 
    """
    cmd = '{} -c {} {} '.format(SOLR_POST_COMMAND, collection, fname)
    output, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return output

# .............................................................................
def post(fname, collection, solr_location, headers=None):
    """Post a document to a Solr index.
    
    Args:
        fname: Full path the file containing data to be indexed in Solr
        collection: name of the Solr collection to be posted to 
        solr_location: URL to solr instance (i.e. http://localhost:8983/solr)
        headers: optional keyword/values to send server
    """
    retcode = 0
    if solr_location is not None:
        retcode, output = _post_remote(fname, collection, solr_location, headers)
    else:
        output = _post_local(fname, collection)
    return retcode, output

# .............................................................................
def query_guid(guid, collection, solr_location):
    """
    Query a Specify resolver index and return results for an occurrence in 
    JSON format.
    
    Args:
        guid: Unique identifier for record of interest
        collection: name of the Solr index
        solr_location: IP or FQDN for solr index

    Return: 
        a dictionary containing one or more keys: count, docs, error
    """
    return query(collection, solr_location, filters={'id': guid})
    
# .............................................................................
def query(collection, solr_location, filters={'*': '*'}):
    """Query a solr index and return results in JSON format
    
    Args:
        collection: solr index for query
        solr_location: IP or FQDN for solr index
        filters: q filters for solr query

    Return: 
        a dictionary containing one or more keys: count, docs, error
    """
    output = {S2nKey.COUNT: 0}
    errmsgs = []
    
    solr_endpt = 'http://{}:8983/solr/{}/select'.format(solr_location, collection)
    api = APIQuery(solr_endpt, q_filters=filters)
    api.query_by_get(output_type='json')
    try:
        response = api.output['response']
    except:
        errmsgs.append('Missing `response` element')
    else:
        try:
            output[S2nKey.COUNT] = response['numFound']
        except:
            errmsgs.append('Failed to return numFound from solr')
        try:
            output[S2nKey.RECORDS] = response['docs']
        except:
            errmsgs.append('Failed to return docs from solr')
    output[S2nKey.ERRORS] = errmsgs
    return output

# .............................................................................
def update(collection, solr_location):
    url = '{}/{}/update'.format(solr_location, collection)
    cmd = '{} {}'.format(CURL_COMMAND, url)
    output, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return output

# .............................................................................
if __name__ == '__main__':
    # test
    doc = count_docs(SPECIFY.RESOLVER_COLLECTION, SPECIFY.RESOLVER_LOCATION)
    print('Found {} records in {}'.format(doc, SPECIFY.RESOLVER_COLLECTION))
    for guid in TST_VALUES.GUIDS_W_SPECIFY_ACCESS:
        doc = query_guid(
            guid, SPECIFY.RESOLVER_COLLECTION, SPECIFY.RESOLVER_LOCATION)
        print('Found {} record for guid {}'.format(doc, guid))

"""
Post:
/opt/solr/bin/post -c spcoco /state/partition1/git/t-rex/data/solrtest/occurrence.solr.csv

Query:
curl http://notyeti-192.lifemapper.org:8983/solr/spcoco/select?q=occurrence_guid:47d04f7e-73fa-4cc7-b50a-89eeefdcd162
curl http://notyeti-192.lifemapper.org:8983/solr/spcoco/select?q=*:*
"""
