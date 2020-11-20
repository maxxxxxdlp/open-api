import os

# hierarchySoFarWRanks <class 'list'>: ['41107:$Kingdom:Plantae$Subkingdom:Viridiplantae$Infrakingdom:Streptophyta$Superdivision:Embryophyta$Division:Tracheophyta$Subdivision:Spermatophytina$Class:Magnoliopsida$Superorder:Lilianae$Order:Poales$Family:Poaceae$Genus:Poa$Species:Poa annua$']
# hierarchyTSN <class 'list'>: ['$202422$954898$846494$954900$846496$846504$18063$846542$846620$40351$41074$41107$']
APP_PATH = '/opt/lifemapper'
CONFIG_DIR = 'config'
TEST_SPECIFY7_SERVER = 'http://preview.specifycloud.org'
TEST_SPECIFY7_RSS_URL = '{}/export/rss'.format(TEST_SPECIFY7_SERVER)

# For saving Specify7 server URL (used to download individual records)
SPECIFY7_SERVER_KEY = 'specify7-server'
SPECIFY7_RECORD_ENDPOINT = 'export/record'

KU_IPT_RSS_URL = 'http://ipt.nhm.ku.edu:8080/ipt/rss.do'
ICH_RSS_URL = 'https://ichthyology.specify.ku.edu/export/rss'

SPECIFY_ARK_PREFIX = 'http://spcoco.org/ark:/'
DWC_URL = 'http://rs.tdwg.org/dwc'
DWC_RECORD_TITLE = 'digital specimen object'

JSON_HEADERS = {'Content-Type': 'application/json'}

class TEST_VALUES:
    FISH_GUIDS = [
        '2c1becd5-e641-4e83-b3f5-76a55206539a', 
        'a413b456-0bff-47da-ab26-f074d9be5219',
        'fa7dd78f-8c91-49f5-b01c-f61b3d30caee',
        'db1af4fe-1ed3-11e3-bfac-90b11c41863e',
        'dbe1622c-1ed3-11e3-bfac-90b11c41863e',
        'dcbdb494-1ed3-11e3-bfac-90b11c41863e',
        'dc92869c-1ed3-11e3-bfac-90b11c41863e',
        '21ac6644-5c55-44fd-b258-67eb66ea231d']
    BIRD_GUIDS = [
        'ed8cfa5a-7b47-11e4-8ef3-782bcb9cd5b5',
        'f5725a56-7b47-11e4-8ef3-782bcb9cd5b5',
        'f69696a8-7b47-11e4-8ef3-782bcb9cd5b5',
        '5e7ec91c-4d20-42c4-ad98-8854800e82f7']
    NAMES = [
        'Acer caesium Wall. ex Brandis', 'Acer heldreichii Orph. ex Boiss.', 
        'Acer pseudoplatanus L.', 'Acer velutinum Boiss.', 
        'Acer hyrcanum Fisch. & Meyer', 'Acer monspessulanum L.', 
        'Acer obtusifolium Sibthorp & Smith', 'Acer opalus Miller', 
        'Acer sempervirens L.', 'Acer floridanum (Chapm.) Pax', 
        'Acer grandidentatum Torr. & Gray', 'Acer leucoderme Small', 
        'Acer nigrum Michx.f.', 'Acer skutchii Rehder', 'Acer saccharum Marshall']
    GUIDS = [526853, 183671, 182662, 566578]
    DATASET_GUIDS = ['56caf05f-1364-4f24-85f6-0c82520c2792']
    BAD_GUIDS = [
        'KU :KUIZ:2200', 'KU :KUIZ:1663', 'KU :KUIZ:1569', 'KU :KUIZ:2462', 
        'KU :KUIZ:1743', 'KU :KUIZ:3019', 'KU :KUIZ:1816', 'KU :KUIZ:2542', 
        'KU :KUIZ:2396']

CHERRYPY_CONFIG_FILE = os.path.join(APP_PATH, CONFIG_DIR, 'cherrypy.conf')

class APIMount:
    # occurrence services
    OccurrenceSvc = '/tentacles/occ'
    SpecifyArk = '/tentacles/sparks'
    GOcc = '/tentacles/occ/gbif'
    IDBOcc = '/tentacles/occ/idb'
    SPOcc = '/tentacles/occ/specify'
    GColl = '/tentacles/occ/gbif/dataset'
    # name services
    NameSvc = '/tentacles/name'
    GAcName = '/tentacles/name/gbif'
    ITISName = '/tentacles/name/itis'
    ITISSolrName = '/tentacles/name/itis2'

class DWCA:
    NS = '{http://rs.tdwg.org/dwc/text/}'
    META_FNAME = 'meta.xml'
    DATASET_META_FNAME = 'eml.xml'
    # Meta.xml element/attribute keys
    DELIMITER_KEY = 'fieldsTerminatedBy'
    LINE_DELIMITER_KEY = 'linesTerminatedBy'
    QUOTE_CHAR_KEY = 'fieldsEnclosedBy'
    LOCATION_KEY = 'location'
    UUID_KEY = 'id'
    FLDMAP_KEY = 'fieldname_index_map'
    FLDS_KEY = 'fieldnames'
    
    CORE_TYPE = '{}/terms/Occurrence'.format(DWC_URL)
    CORE_FIELDS_OF_INTEREST = [
        'id',
        'institutionCode',
        'collectionCode',
        'datasetName',
        'basisOfRecord',
        'year',
        'month',
        'day']

URL_ESCAPES = [[" ", "\%20"], [",", "\%2C"]]
ENCODING = 'utf-8'

DWC_QUALIFIER = 'dwc:'

"""  
http://preview.specifycloud.org/static/depository/export_feed/kui-dwca.zip
http://preview.specifycloud.org/static/depository/export_feed/kuit-dwca.zip

curl '{}{}'.format(http://preview.specifycloud.org/export/record/
  | python -m json.tool

"""

# .............................................................................
# These fields must match the Solr core fields in spcoco/conf/schema.xml
SPCOCO_FIELDS = [
    # GUID and solr uniqueKey
    'id',
    # pull dataset/alternateIdentfier from DWCA eml.xml
    'dataset_guid',
    # ARK metadata
    # similar to DC Creator, Contributor, Publisher
    'who',
    # similar to DC Title
    'what',
    # similar to DC Date
    'when',
    # similar to DC Identifier, optional as this is the ARK
    'where',
    # Supplemental ARK metadata
    # redirection URL to specify7-server
    'url']

# For parsing BISON Solr API response, updated Feb 2015
class BISON:
    """Bison constant enumeration
    """
    OCCURRENCE_URL = 'https://bison.usgs.gov/solr/occurrences/select'
    # Ends in : to allow appending unique id
    LINK_PREFIX = ('https://bison.usgs.gov/solr/occurrences/select/' +
                   '?q=occurrenceID:')
    LINK_FIELD = 'bisonurl'
    # For TSN query filtering on Binomial
    NAME_KEY = 'ITISscientificName'
    # For Occurrence query by TSN in hierarchy
    HIERARCHY_KEY = 'hierarchy_homonym_string'
    KINGDOM_KEY = 'kingdom'
    TSN_KEY = 'TSNs'
    # To limit query
    MIN_POINT_COUNT = 20
    MAX_POINT_COUNT = 5000000
    BBOX = (24, -125, 50, -66)
    BINOMIAL_REGEX = '/[A-Za-z]*[ ]{1,1}[A-Za-z]*/'

# .............................................................................
class BisonQuery:
    """BISON query constants enumeration"""
    # Expected Response Dictionary Keys
    TSN_LIST_KEYS = ['facet_counts', 'facet_fields', BISON.TSN_KEY]
    RECORD_KEYS = ['response', 'docs']
    COUNT_KEYS = ['response', 'numFound']
    TSN_FILTERS = {'facet': True,
                   'facet.limit': -1,
                   'facet.mincount': BISON.MIN_POINT_COUNT,
                   'facet.field': BISON.TSN_KEY,
                   'rows': 0}
    OCC_FILTERS = {'rows': BISON.MAX_POINT_COUNT}
    # Common Q Filters
    QFILTERS = {'decimalLatitude': (BISON.BBOX[0], BISON.BBOX[2]),
                'decimalLongitude': (BISON.BBOX[1], BISON.BBOX[3]),
                'basisOfRecord': [(False, 'living'), (False, 'fossil')]}
    # Common Other Filters
    FILTERS = {'wt': 'json',
               'json.nl': 'arrarr'}
#     RESPONSE_FIELDS = {
#         'ITIScommonName': ('comname', OFTString),
#         BISON.NAME_KEY: (DwcNames.SCIENTIFIC_NAME['SHORT'], OFTString),
#         'ITIStsn': ('itistsn', OFTInteger),
#         BISON.TSN_KEY: None,
#         'ambiguous': None,
#         DwcNames.BASIS_OF_RECORD['FULL']: (
#             DwcNames.BASIS_OF_RECORD['SHORT'], OFTString),
#         'calculatedCounty': ('county', OFTString),
#         'calculatedState': ('state', OFTString),
#         DwcNames.CATALOG_NUMBER['FULL']: (
#             DwcNames.CATALOG_NUMBER['SHORT'], OFTString),
#         'collectionID': ('coll_id', OFTString),
#         'computedCountyFips': None,
#         'computedStateFips': None,
#         DwcNames.COUNTRY_CODE['FULL']: (
#             DwcNames.COUNTRY_CODE['SHORT'], OFTString),
#         DwcNames.DECIMAL_LATITUDE['FULL']: (
#             DwcNames.DECIMAL_LATITUDE['SHORT'], OFTReal),
#         DwcNames.DECIMAL_LONGITUDE['FULL']: (
#             DwcNames.DECIMAL_LONGITUDE['SHORT'], OFTReal),
#         'eventDate': ('date', OFTString),
#         # Space delimited, same as latlon
#         'geo': None,
#         BISON.HIERARCHY_KEY: ('tsn_hier', OFTString),
#         'institutionID': ('inst_id', OFTString),
#         BISON.KINGDOM_KEY: ('kingdom', OFTString),
#         # Comma delimited, same as geo
#         'latlon': ('latlon', OFTString),
#         DwcNames.OCCURRENCE_ID['FULL']: (
#             DwcNames.OCCURRENCE_ID['SHORT'], OFTInteger),
#         'ownerInstitutionCollectionCode': (PROVIDER_FIELD_COMMON, OFTString),
#         'pointPath': None,
#         'providedCounty': None,
#         'providedScientificName': None,
#         'providerID': None,
#         DwcNames.RECORDED_BY['FULL']: (
#             DwcNames.RECORDED_BY['SHORT'], OFTString),
#         'resourceID': None,
#         # Use ITIS Scientific Name
#         'scientificName': None,
#         'stateProvince': ('stprov', OFTString),
#         DwcNames.YEAR['SHORT']: (DwcNames.YEAR['SHORT'], OFTInteger),
#         # Very long integer
#         '_version_': None
#     }

# ......................................................
class MorphoSource:
    URL = 'http://www.morphosource.org/api/v1'
    OCC_RESOURCE = 'specimens'
    MEDIA_RESOURCE = 'media'
    OTHER_RESOURCES = ['taxonomy', 'projects', 'facilities']
    COMMAND = 'find'
    OCCURRENCEID_KEY = 'occurrence_id'
    
# ......................................................
class SPECIFY:
    """Specify constants enumeration
    """
    DATA_DUMP_DELIMITER = '\t'
    
# ......................................................
class GBIF:
    """GBIF constants enumeration"""
    DATA_DUMP_DELIMITER = '\t'
    TAXON_KEY = 'specieskey'
    TAXON_NAME = 'sciname'
    PROVIDER = 'puborgkey'
    GBIFID = 'gbifid'
    WAIT_TIME = 180
    LIMIT = 300
    REST_URL = 'http://api.gbif.org/v1'
    QUALIFIER = 'gbif:'

    SPECIES_SERVICE = 'species'
    PARSER_SERVICE = 'parser/name'
    OCCURRENCE_SERVICE = 'occurrence'
    DATASET_SERVICE = 'dataset'
    ORGANIZATION_SERVICE = 'organization'

    TAXONKEY_FIELD = 'specieskey'
    TAXONNAME_FIELD = 'sciname'
    PROVIDER_FIELD = 'puborgkey'
    ID_FIELD = 'gbifid'

    ACCEPTED_NAME_KEY = 'accepted_name'
    SEARCH_NAME_KEY = 'search_name'
    SPECIES_KEY_KEY = 'speciesKey'
    SPECIES_NAME_KEY = 'species'
    TAXON_ID_KEY = 'taxon_id'

    REQUEST_SIMPLE_QUERY_KEY = 'q'
    REQUEST_NAME_QUERY_KEY = 'name'
    REQUEST_TAXON_KEY = 'TAXON_KEY'
    REQUEST_RANK_KEY = 'rank'
    REQUEST_DATASET_KEY = 'dataset_key'

    DATASET_BACKBONE_VALUE = 'GBIF Backbone Taxonomy'
    DATASET_BACKBONE_KEY = 'd7dddbf4-2cf0-4f39-9b2a-bb099caae36c'

    SEARCH_COMMAND = 'search'
    COUNT_COMMAND = 'count'
    MATCH_COMMAND = 'match'
    DOWNLOAD_COMMAND = 'download'
    DOWNLOAD_REQUEST_COMMAND = 'request'
    RESPONSE_NOMATCH_VALUE = 'NONE'
    
    NameMatchFieldnames = [
        'scientificName', 'kingdom', 'phylum', 'class', 'order', 'family',
        'genus', 'species', 'rank', 'genusKey', 'speciesKey', 'usageKey',
        'canonicalName', 'confidence']

    # For writing files from GBIF DarwinCore download,
    # DWC translations in lmCompute/code/sdm/gbif/constants
    # We are adding the 2 fields: LM_WKT_FIELD and LINK_FIELD
    LINK_FIELD = 'gbifurl'
    # Ends in / to allow appending unique id
    LINK_PREFIX = 'http://www.gbif.org/occurrence/'



# .............................................................................
class Itis:
    """ITIS constants enumeration
    http://www.itis.gov/ITISWebService/services/ITISService/getAcceptedNamesFromTSN?tsn=183671
    @todo: for JSON output use jsonservice instead of ITISService
    """
    DATA_NAMESPACE = '{http://data.itis_service.itis.usgs.gov/xsd}'
    NAMESPACE = '{http://itis_service.itis.usgs.gov}'
    # ...........
    # Solr Services
    SOLR_URL = 'https://services.itis.gov/'
    TAXONOMY_HIERARCHY_QUERY = 'getFullHierarchyFromTSN'
    VERNACULAR_QUERY = 'getCommonNamesFromTSN'    
    NAMES_FROM_TSN_QUERY = 'getAcceptedNamesFromTSN'
    # ...........
    # Web Services
    WEBSVC_URL = 'http://www.itis.gov/ITISWebService/services/ITISService'
    JSONSVC_URL = 'https://www.itis.gov/ITISWebService/jsonservice'
    # wildcard matching
    ITISTERMS_FROM_SCINAME_QUERY = 'getITISTermsFromScientificName'
    SEARCH_KEY = 'srchKey'
    # JSON return tags
    TSN_KEY = 'tsn'
    NAME_KEY = 'nameWOInd'
    HIERARCHY_KEY = 'hierarchySoFarWRanks'
    HIERARCHY_TAG = 'hierarchyList'
    RANK_TAG = 'rankName'
    TAXON_TAG = 'taxonName'
    KINGDOM_KEY = 'Kingdom'
    PHYLUM_DIVISION_KEY = 'Division'
    CLASS_KEY = 'Class'
    ORDER_KEY = 'Order'
    FAMILY_KEY = 'Family'
    GENUS_KEY = 'Genus'
    SPECIES_KEY = 'Species'
    URL_ESCAPES = [ [" ", "\%20"] ]

# .............................................................................
# .                           iDigBio constants                               .
# .............................................................................
class Idigbio:
    """iDigBio constants enumeration
    """
    LINK_PREFIX = 'https://www.idigbio.org/portal/records/'
    SEARCH_PREFIX = 'https://search.idigbio.org/v2'
    SEARCH_POSTFIX = 'search'
    OCCURRENCE_POSTFIX = 'records'
    PUBLISHERS_POSTFIX = 'publishers'
    RECORDSETS_POSTFIX = 'recordsets'
    SEARCH_LIMIT = 5000
    ID_FIELD = 'uuid'
    OCCURRENCEID_FIELD = 'occurrenceid'
    LINK_FIELD = 'idigbiourl'
    GBIFID_FIELD = 'taxonid'
    BINOMIAL_REGEX = "(^[^ ]*) ([^ ]*)$"
    OCCURRENCE_ITEMS_KEY = 'items'
    RECORD_CONTENT_KEY = 'data'
    RECORD_INDEX_KEY = 'indexTerms'
    QUALIFIER = 'idigbio:'
    QKEY = 'rq'
    QFILTERS = {'basisofrecord': 'preservedspecimen'}
    FILTERS = {'limit': 5000,
               'offset': 0,
               'no_attribution': False}
    

# .............................................................................
class HTTPStatus:
    """HTTP 1.1 Status Codes

    See:
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
    """
    # Informational 1xx
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    # Successful 2xx
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    # Redirectional 3xx
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 204
    USE_PROXY = 305
    TEMPORARY_REDIRECT = 307
    # Client Error 4xx
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    REQUEST_ENTITY_TOO_LARGE = 413
    REQUEST_URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    REQUEST_RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    # Server Error 5xx
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505


