SPECIFY_URL = 'http://preview.specifycloud.org/'
PUBLIC_PREFIX = 'export'

ARK_PREFIX = 'http://spcoco.org/ark:/'
REC_URL = '{}/{}/record'.format(SPECIFY_URL, PUBLIC_PREFIX)
RSS_URL = '{}/{}/rss'.format(SPECIFY_URL, PUBLIC_PREFIX)
EXPORT_URL = '{}/static/depository/export_feed'.format(SPECIFY_URL)
DWC_URL = 'http://rs.tdwg.org/dwc'
DWC_RECORD_TITLE = 'digital specimen object'

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

URL_ESCAPES = [[" ", "%20"], [",", "%2C"]]
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
    # redirection URL
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
class SPECIFY:
    """Specify constants enumeration
    """
    DATA_DUMP_DELIMITER = '\t'
    
# ......................................................
class GBIF:
    """GBIF constants enumeration
    """
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

    REQUEST_SIMPLE_QUERY_KEY = 'q'
    REQUEST_NAME_QUERY_KEY = 'name'
    REQUEST_TAXON_KEY = 'TAXON_KEY'
    REQUEST_RANK_KEY = 'rank'
    REQUEST_DATASET_KEY = 'dataset_key'

    DATASET_BACKBONE_VALUE = 'GBIF Backbone Taxonomy'

    SEARCH_COMMAND = 'search'
    COUNT_COMMAND = 'count'
    MATCH_COMMAND = 'match'
    DOWNLOAD_COMMAND = 'download'
    DOWNLOAD_REQUEST_COMMAND = 'request'
    RESPONSE_IDENTIFIER_KEY = 'key'
    RESPONSE_RESULT_KEY = 'results'
    RESPONSE_END_KEY = 'endOfRecords'
    RESPONSE_COUNT_KEY = 'count'
    RESPONSE_GENUS_ID_KEY = 'genusKey'
    RESPONSE_GENUS_KEY = 'genus'
    RESPONSE_SPECIES_ID_KEY = 'speciesKey'
    RESPONSE_SPECIES_KEY = 'species'
    RESPONSE_MATCH_KEY = 'matchType'
    RESPONSE_NOMATCH_VALUE = 'NONE'

    # For writing files from GBIF DarwinCore download,
    # DWC translations in lmCompute/code/sdm/gbif/constants
    # We are adding the 2 fields: LM_WKT_FIELD and LINK_FIELD
    LINK_FIELD = 'gbifurl'
    # Ends in / to allow appending unique id
    LINK_PREFIX = 'http://www.gbif.org/occurrence/'



# .............................................................................
class Itis:
    """ITIS constants enumeration
    """
    DATA_NAMESPACE = 'http://data.itis_service.itis.usgs.gov/xsd'
    # Basic Web Services
    TAXONOMY_HIERARCHY_URL = ('http://www.itis.gov/ITISWebService/services/' +
                              'ITISService/getFullHierarchyFromTSN')
    # JSON Web Services
    TAXONOMY_KEY = 'tsn'
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
    SPECIFY_GUID_FIELD = 'occurrenceid'
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


