import os
import requests
import urllib

from LmRex.common.lmconstants import (
    APIService, GBIF, ServiceProvider, URL_ESCAPES, ENCODING, TST_VALUES)
from LmRex.fileop.logtools import (log_info, log_error)

from LmRex.services.api.v1.s2n_type import S2nKey, S2nOutput
from LmRex.tools.provider.api import APIQuery

# .............................................................................
class GbifAPI(APIQuery):
    """Class to query GBIF APIs and return results"""
    PROVIDER = ServiceProvider.GBIF['name']
    # ...............................................
    def __init__(self, service=GBIF.SPECIES_SERVICE, key=None,
                 other_filters=None, logger=None):
        """
        Constructor for GbifAPI class
        
        Args:
            service: GBIF service to query
            key: unique identifier for an object of this service
            other_filters: optional filters
            logger: optional logger for info and error messages.  If None, 
                prints to stdout
        """
        url = '/'.join((GBIF.REST_URL, service))
        if key is not None:
            url = '/'.join((url, str(key)))
        APIQuery.__init__(self, url, other_filters=other_filters, logger=logger)

    # ...............................................
    def _assemble_filter_string(self, filter_string=None):
        # Assemble key/value pairs
        if filter_string is None:
            all_filters = self._other_filters.copy()
            if self._q_filters:
                q_val = self._assemble_q_val(self._q_filters)
                all_filters[self._q_key] = q_val
            for k, val in all_filters.items():
                if isinstance(val, bool):
                    val = str(val).lower()
                # works for GBIF, iDigBio, ITIS web services (no manual escaping)
                all_filters[k] = str(val).encode(ENCODING)
            filter_string = urllib.parse.urlencode(all_filters)
        # Escape filter string
        else:
            for oldstr, newstr in URL_ESCAPES:
                filter_string = filter_string.replace(oldstr, newstr)
        return filter_string

    # ...............................................
    @classmethod
    def _get_output_val(cls, out_dict, name):
        try:
            tmp = out_dict[name]
            val = str(tmp).encode(ENCODING)
        except Exception:
            return None
        return val

    # ...............................................
    @classmethod
    def get_taxonomy(cls, taxon_key, logger=None):
        """Return GBIF backbone taxonomy for this GBIF Taxon ID
        """
        std_output = {S2nKey.COUNT: 0}
        errmsgs = []
        std_recs = []
        rec = {}
        tax_api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key=taxon_key, logger=logger)
        try:
            tax_api.query()
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            output = tax_api.output
            elements_of_interest = [
                'scientificName', 'kingdom', 'phylum', 'class', 'order', 
                'family', 'genus', 'species', 'rank', 'genusKey', 'speciesKey', 
                'taxonomicStatus', 'canonicalName', 'scientificName', 'kingdom', 
                'phylum', 'class', 'order', 'family', 'genus', 'species', 
                'rank', 'genusKey', 'speciesKey', 'taxonomicStatus', 
                'canonicalName', 'acceptedKey', 'accepted', 'nubKey']
            for fld in elements_of_interest:
                rec[fld] = tax_api._get_output_val(output, fld)
            std_recs.append(rec)
            
        std_output[S2nKey.RECORDS] = std_recs
        std_output[S2nKey.ERRORS] = errmsgs
        return std_output

    # ...............................................
    @classmethod
    def get_occurrences_by_occid(cls, occid, count_only=False, logger=None):
        """Return GBIF occurrences for this occurrenceId.  This should retrieve 
        a single record if the occurrenceId is unique.
        
        Args:
            occid: occurrenceID for query
            count_only: boolean flag signaling to return records or only count
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning
                
        Todo: enable paging
        """
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={'occurrenceID': occid}, logger=logger)
        try:
            api.query()
        except Exception as e:
            out = cls.get_failure(
                query_term=occid, errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_output(
                api.output, GBIF.COUNT_KEY, GBIF.RECORDS_KEY, 
                GBIF.RECORD_FORMAT_OCCURRENCE, count_only=count_only, 
                err=api.error)
        
        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[api.url], query_term=occid, 
            service=APIService.Occurrence)
        return full_out

    # ...............................................
    @classmethod
    def _get_fld_vals(cls, big_rec):
        rec = {}
        for fld_name in GbifAPI.NameMatchFieldnames:
            try:
                rec[fld_name] = big_rec[fld_name]
            except KeyError:
                pass
        return rec

    # ...............................................
    @classmethod
    def _standardize_gbif_occurrence(cls, rec):
        # todo: standardize gbif output to DWC, DSO, etc
        return rec
    
    # ...............................................
    @classmethod
    def _standardize_gbif_name(cls, rec):
        # todo: standardize gbif output
        return rec
    
    # ...............................................
    @classmethod
    def _test_record(cls, status, rec):
        is_good = False
        # No filter by status, take original
        if status is None:
            is_good = True
        else:
            outstatus = None
            try:
                outstatus = rec['status'].lower()
            except AttributeError:
                print(cls._get_error_message(msg='No status in record'))
            else:
                if outstatus == status:
                    is_good = True
        return is_good
        
    # ...............................................
    @classmethod
    def _standardize_match_output(cls, output, status, err=None):
            # Pull alternatives out of record
        stdrecs = []
        errmsgs = []
        if err:
            errmsgs.append(err)
        try:
            alternatives = output.pop('alternatives')
        except:
            alternatives = []
            
        is_match = True
        try:
            if output['matchType'].lower() == 'none':
                is_match = False
        except AttributeError:
            errmsgs.append(cls._get_error_message(msg='No matchType'))
        else:
            goodrecs = []
            # take primary output if matched
            if is_match:
                if cls._test_record(status, output):
                    goodrecs.append(output)
            for alt in alternatives:
                if cls._test_record(status, alt):
                    goodrecs.append(alt)
            # Standardize name output
            for r in goodrecs:
                stdrecs.append(cls._standardize_gbif_name(r))
        total = len(stdrecs)
        # TODO: standardize_record and provide schema link
        std_output = S2nOutput(
            count=total, record_format=GBIF.RECORD_FORMAT_NAME, records=stdrecs, 
            provider=cls.PROVIDER, errors=errmsgs, 
            provider_query=None, query_term=None, service=None)
        return std_output
        
    # ...............................................
    @classmethod
    def _standardize_record(cls, rec, record_format):
        # todo: standardize gbif output to DWC, DSO, etc
        if record_format == GBIF.RECORD_FORMAT_OCCURRENCE:
            return cls._standardize_gbif_occurrence(rec)
        else:
            return cls._standardize_gbif_name(rec)
    
    # ...............................................
    @classmethod
    def _standardize_output(
            cls, output, count_key, records_key, record_format, count_only=False, err=None):
        stdrecs = []
        total = 0
        errmsgs = []
        if err is not None:
            errmsgs.append(err)
        # Count
        try:
            total = output[count_key]
        except:
            errmsgs.append(
                cls._get_error_message(
                    msg='Missing `{}` element'.format(count_key)))
        # Records
        if not count_only:
            try:
                recs = output[records_key]
            except:
                errmsgs.append(
                    cls._get_error_message(
                        msg='Missing `{}` element'.format(records_key)))
            else:
                stdrecs = []
                for r in recs:
                    try:
                        stdrecs.append(
                            cls._standardize_record(r, record_format))
                    except Exception as e:
                        msg = cls._get_error_message(err=e)
                        errmsgs.append(msg)
        std_output = S2nOutput(
            count=total, record_format=record_format, records=stdrecs, 
            provider=cls.PROVIDER, errors=errmsgs, 
            provider_query=None, query_term=None, service=None)

        return std_output
    
    # ...............................................
    @classmethod
    def get_occurrences_by_dataset(
            cls, dataset_key, count_only, logger=None):
        """
        Count and optionally return (a limited number of) records with the given 
        dataset_key.
        
        Args:
            dataset_key: unique identifier for the dataset, assigned by GBIF
                and retained by Specify
            count_only: boolean flag signaling to return records or only count
            logger: optional logger for info and error messages.  If None, 
                prints to stdout    

        Return: 
            a dictionary containing one or more keys: 
                count, records, error, warning
        
        Todo: 
            handle large queries asynchronously
        """
        if count_only is True:
            limit = 1
        else:
            limit = GBIF.LIMIT   
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={
                'dataset_key': dataset_key, 'offset': 0, 
                'limit': limit}, logger=logger)
        try:
            api.query()
        except Exception as e:
            out = cls.get_failure(
                query_term=dataset_key, errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_output(
                api.output, GBIF.COUNT_KEY, GBIF.RECORDS_KEY, 
                GBIF.RECORD_FORMAT_OCCURRENCE, count_only=count_only, 
                err=api.error)
            
        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[api.url], query_term=dataset_key, 
            service=APIService.Dataset)
        return full_out


    # ...............................................
    @classmethod
    def match_name(cls, namestr, status=None, logger=None):
        """Return closest accepted species in GBIF backbone taxonomy,
        
        Args:
            namestr: A scientific namestring possibly including author, year, 
                rank marker or other name information.
            status: optional constant to match the TaxonomicStatus in the GBIF
                record
                
        Returns:
            Either a dictionary containing a matching record with status 
                'accepted' or 'synonym' without 'alternatives'.  
            Or, if there is no matching record, return the first/best 
                'alternative' record with status 'accepted' or 'synonym'.

        Note:
            This function uses the name search API, 
        """
        name_clean = namestr.strip()
        other_filters = {'name': name_clean, 'verbose': 'true'}
#         if rank:
#             other_filters['rank'] = rank
#         if kingdom:
#             other_filters['kingdom'] = kingdom
        api = GbifAPI(
            service=GBIF.SPECIES_SERVICE, key='match',
            other_filters=other_filters, logger=logger)
        
        try:
            api.query()
        except Exception as e:
            out = cls.get_failure(
                query_term=namestr, errors=[cls._get_error_message(err=e)])
        else:
            # Standardize output from provider response
            out = cls._standardize_match_output(
                api.output, status, err=api.error)
            
        full_out = S2nOutput(
            count=out.count, record_format=out.record_format, 
            records=out.records, provider=cls.PROVIDER, errors=out.errors, 
            provider_query=[api.url], query_term=namestr, service=APIService.Name)
        return full_out


    # ...............................................
    @classmethod
    def count_occurrences_for_taxon(cls, taxon_key, logger=None):
        """Return a count of occurrence records in GBIF with the indicated taxon.
                
        Args:
            taxon_key: A GBIF unique identifier indicating a taxon object.
                
        Returns:
            A record as a dictionary containing the record count of occurrences
            with this accepted taxon, and a URL to retrieve these records.            
        """
        simple_output = {}
        errmsgs = []
        total = 0
        # Query GBIF
        api = GbifAPI(
            service=GBIF.OCCURRENCE_SERVICE, key=GBIF.SEARCH_COMMAND,
            other_filters={'taxonKey': taxon_key}, logger=logger)
        
        try:
            api.query_by_get()
        except Exception as e:
            errmsgs.append(cls._get_error_message(err=e))
        else:
            try:
                total = api.output['count']
            except Exception as e:
                errmsgs.append(cls._get_error_message(
                    msg='Missing `count` element'))
            else:
                if total < 1:
                    errmsgs.append(cls._get_error_message(msg='No match'))
                    simple_output[S2nKey.OCCURRENCE_URL] = None
                else:
                    simple_output[S2nKey.OCCURRENCE_URL] = '{}/{}'.format(
                        GBIF.SPECIES_URL, taxon_key)
        # TODO: standardize_record and provide schema link
        simple_output[S2nKey.COUNT] = total
        simple_output[S2nKey.QUERY_TERM] = taxon_key
        simple_output[S2nKey.RECORD_FORMAT] = None
        simple_output[S2nKey.RECORDS] = []
        simple_output[S2nKey.PROVIDER] = cls.PROVIDER
        simple_output[S2nKey.PROVIDER_QUERY] = [api.url]
        simple_output[S2nKey.ERRORS] = errmsgs
        return simple_output

    # ......................................
    @classmethod
    def _post_json_to_parser(cls, url, data, logger=None):
        response = output = None
        try:
            response = requests.post(url, json=data)
        except Exception as e:
            if response is not None:
                ret_code = response.status_code
            else:
                log_error('Failed on URL {} ({})'.format(url, str(e)), 
                          logger=logger)
        else:
            if response.ok:
                try:
                    output = response.json()
                except Exception as e:
                    try:
                        output = response.content
                    except Exception:
                        output = response.text
                    else:
                        log_error(
                            'Failed to interpret output of URL {} ({})'.format(
                                url, str(e)), logger=logger)
            else:
                try:
                    ret_code = response.status_code
                    reason = response.reason
                except AttributeError:
                    log_error(
                        'Failed to find failure reason for URL {} ({})'.format(
                            url, str(e)), logger=logger)
                else:
                    log_error(
                        'Failed on URL {} ({}: {})'.format(url, ret_code, reason), 
                        logger=logger)
        return output
    
    
# ...............................................
    @classmethod
    def _trim_parsed_output(cls, output, logger=None):
        recs = []
        for rec in output:
            # Only return parsed records
            try:
                success = rec['parsed']
            except:
                log_error('Missing `parsed` field in record', logger=logger)
            else:
                if success:
                    recs.append(rec)
        return recs

# ...............................................
    @classmethod
    def parse_name(cls, namestr, logger=None):
        """
        Send a scientific name to the GBIF Parser returning a canonical name.
        
        Args:
            namestr: A scientific namestring possibly including author, year, 
                rank marker or other name information.
                
        Returns:
            A dictionary containing a single record for a parsed scientific name
            and any optional error messages.
            
        sent (bad) http://api.gbif.org/v1/parser/name?name=Acer%5C%2520caesium%5C%2520Wall.%5C%2520ex%5C%2520Brandis
        send good http://api.gbif.org/v1/parser/name?name=Acer%20heldreichii%20Orph.%20ex%20Boiss.
        """
        output = {}
        # Query GBIF
        name_api = GbifAPI(
            service=GBIF.PARSER_SERVICE, 
            other_filters={GBIF.REQUEST_NAME_QUERY_KEY: namestr},
            logger=logger)
        name_api.query_by_get()
        # Parse results (should be only one)
        if name_api.output is not None:
            recs = name_api._trim_parsed_output(name_api.output)
            try:
                output['record'] = recs[0]
            except:
                msg = 'Failed to return results from {}, ({})'.format(
                    name_api.url, cls.__class__.__name__)
                log_error(msg, logger=logger)
                output[S2nKey.ERRORS] = msg
        return output

    # ...............................................
    @classmethod
    def parse_names(cls, names=[], filename=None, logger=None):
        """
        Send a list or file (or both) of scientific names to the GBIF Parser,
        returning a dictionary of results.  Each scientific name can possibly 
        include author, year, rank marker or other name information.
        
        Args:
            names: a list of names to be parsed
            filename: a file of names to be parsed
            
        Returns:
            A list of resolved records, each is a dictionary with keys of 
            GBIF fieldnames and values with field values. 
        """
        if filename and os.path.exists(filename):
            with open(filename, 'r', encoding=ENCODING) as in_file:
                for line in in_file:
                    names.append(line.strip())

        url = '{}/{}'.format(GBIF.REST_URL, GBIF.PARSER_SERVICE)
        try:
            output = GbifAPI._post_json_to_parser(url, names, logger=logger)
        except Exception as e:
            log_error(
                'Failed to get response from GBIF for data {}, {}'.format(
                    filename, e), logger=logger)
            raise e

        if output:
            recs = GbifAPI._trim_parsed_output(output, logger=logger)
            if filename is not None:
                log_info(
                    'Wrote {} parsed records from GBIF to file {}'.format(
                        len(recs), filename), logger=logger)
            else:
                log_info(
                    'Found {} parsed records from GBIF for {} names'.format(
                        len(recs), len(names)), logger=logger)

        return recs

    # ...............................................
    @classmethod
    def get_publishing_org(cls, pub_org_key, logger=None):
        """Return title from one organization record with this key

        Args:
            pub_org_key: GBIF identifier for this publishing organization
        """
        org_api = GbifAPI(
            service=GBIF.ORGANIZATION_SERVICE, key=pub_org_key, logger=logger)
        try:
            org_api.query()
            pub_org_name = org_api._get_output_val(org_api.output, 'title')
        except Exception as e:
            log_error(str(e), logger=logger)
            raise
        return pub_org_name

    # ...............................................
    def query(self):
        """ Queries the API and sets 'output' attribute to a ElementTree object
        """
        APIQuery.query_by_get(self, output_type='json')



# .............................................................................
def test_gbif():
    """Test GBIF
    """
    taxon_id = 1000225
    output = GbifAPI.get_taxonomy(taxon_id)
    log_info('GBIF Taxonomy for {} = {}'.format(taxon_id, output))


# .............................................................................
def test_idigbio_taxon_ids():
    """Test iDigBio taxon ids
    """
    in_f_name = '/tank/data/input/idigbio/taxon_ids.txt'
    test_count = 20

    out_list = '/tmp/idigbio_accepted_list.txt'
    if os.path.exists(out_list):
        os.remove(out_list)
    out_f = open(out_list, 'w', encoding=ENCODING)

    idig_list = []
    with open(in_f_name, 'r', encoding=ENCODING) as in_f:
        #          with line in file:
        for _ in range(test_count):
            line = in_f.readline()

            if line is not None:
                temp_vals = line.strip().split()
                if len(temp_vals) < 3:
                    log_error(('Missing data in line {}'.format(line)))
                else:
                    try:
                        curr_gbif_taxon_id = int(temp_vals[0])
                    except Exception:
                        pass
                    try:
                        curr_reported_count = int(temp_vals[1])
                    except Exception:
                        pass
                    temp_vals = temp_vals[1:]
                    temp_vals = temp_vals[1:]
                    curr_name = ' '.join(temp_vals)

                output = GbifAPI.get_taxonomy(curr_gbif_taxon_id)
                tax_status = output[6]

                if tax_status == 'ACCEPTED':
                    idig_list.append(
                        [curr_gbif_taxon_id, curr_reported_count, curr_name])
                    out_f.write(line)

    out_f.close()
    return idig_list


# .............................................................................
if __name__ == '__main__':
    # test
    

    namestr = TST_VALUES.NAMES[0]
    clean_names = GbifAPI.parse_names(names=TST_VALUES.NAMES)
    can_name = GbifAPI.parse_name(namestr)
    try:
        acc_name = can_name['canonicalName']
    except Exception as e:
        log_error('Failed to match {}'.format(namestr))
    else:
        acc_names = GbifAPI.match_name(acc_name, status='accepted')
        log_info('Matched accepted names:')
        for n in acc_names:
            log_info('{}: {}, {}'.format(
                n['scientificName'], n['status'], n['rank']))
        log_info ('')
        syn_names = GbifAPI.match_name(acc_name, status='synonym')
        log_info('Matched synonyms:')
        for n in syn_names:
            log_info('{}: {}, {}'.format(
                n['scientificName'], n['status'], n['rank']))
        log_info ('')
        
        names = ['ursidae', 'Poa annua']
        recs = GbifAPI.get_occurrences_by_dataset(TST_VALUES.DS_GUIDS_W_SPECIFY_ACCESS_RECS[0])
        log_info('Returned {} records for dataset:'.format(len(recs)))
        names = ['Poa annua']
        for name in names:
            pass
            good_names = GbifAPI.match_name(
                name, match_backbone=True, rank='species')
            log_info('Matched {} with {} GBIF names:'.format(name, len(good_names)))
            for n in good_names:
                log_info('{}: {}, {}'.format(
                    n['scientificName'], n['status'], n['rank']))
            log_info ('')
