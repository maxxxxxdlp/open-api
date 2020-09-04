from dataclean.tools import get_csv_dict_reader, get_csv_writer, ENCODING

in_fieldnames = [
    'taxonID', 
    'datasetID', 
    'parentNameUsageID', 
    'acceptedNameUsageID', 
    'originalNameUsageID', 
    'scientificName', 
    'scientificNameAuthorship', 
    'canonicalName', 
    'genericName', 
    'specificEpithet', 
    'infraspecificEpithet', 
    'taxonRank', 
    'nameAccordingTo', 
    'namePublishedIn', 
    'taxonomicStatusnomenclaturalStatus', 
    'taxonRemarks', 
    'kingdom', 
    'phylum', 
    'class', 
    'order', 
    'family', 
    'genus'
    ]
out_fieldnames = [
    'canonical_name',
    'accepted_name',
    'canonical_gbif_taxon_id',
    'accepted_gbif_taxon_id',
    ] 
no_accepted_name_id = -999

in_filename = '/tank/data/gbif/taxonomy/Taxon.tsv'
out_filename = '/tank/data/gbif/taxonomy/canonical_to_accepted_allranks.csv'

rdr, inf = get_csv_dict_reader(
    in_filename, '\t', ENCODING, fieldnames=in_fieldnames)

non_accepted_name = {}
accepted_name = {}
try:
    for rec in rdr:
        rank = rec['taxonRank']
#         if rank == 'species':
        tid = rec['taxonID']
        name = rec['canonicalName']
        status = rec['taxonomicStatusnomenclaturalStatus']
        accid = rec['acceptedNameUsageID']
        if status == 'accepted':
            accepted_name[tid] = name
        elif accid:
            non_accepted_name[tid] = (name, accid)
        else:
            non_accepted_name[tid] = (name, no_accepted_name_id)
except Exception as e:
    print('Failed to read {}, {}'.format(in_filename, e))
finally:
    inf.close()
    
wtr, outf = get_csv_writer(out_filename, ',', ENCODING, fmode='w')
wtr.writerow(out_fieldnames)
try:
    for tid, accname in accepted_name.items():
        row = [accname, accname, tid, tid]
        wtr.writerow(row)
    for tid, (name, accid) in non_accepted_name.items():
        try:
            accname = accepted_name[accid]
        except:
            accname = ''
        row = [name, accname, tid, accid]
        wtr.writerow(row)
except Exception as e:
    print('Failed to write {}, {}'.format(out_filename, e))
finally:
    outf.close()
    
        