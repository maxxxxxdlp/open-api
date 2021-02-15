import csv
from multiprocessing import cpu_count
import os
import subprocess
from sys import maxsize

# from common.constants import (LOG_FORMAT, LOG_DATE_FORMAT, LOGFILE_MAX_BYTES,
#                               LOGFILE_BACKUP_COUNT, EXTRA_VALS_KEY)
EXTRA_VALS_KEY = 'rest'
ENCODING = 'utf-8'
# ANCILLARY_DELIMITER = ','
# BISON_DELIMITER = '$'
# PROVIDER_DELIMITER = '\t'
# NEWLINE = '\n'
# LEGACY_ID_DEFAULT = '-9999'
LOG_FORMAT = ' '.join(["%(asctime)s",
                       "%(funcName)s",
                       "line",
                       "%(lineno)d",
                       "%(levelname)-8s",
                       "%(message)s"])
LOG_DATE_FORMAT = '%d %b %Y %H:%M'
LOGFILE_MAX_BYTES = 52000000 
LOGFILE_BACKUP_COUNT = 5

REQUIRED_FIELDS = ['STATE_NAME', 'NAME', 'STATE_FIPS', 'CNTY_FIPS', 'PRNAME', 
     'CDNAME', 'CDUID']
CENTROID_FIELD = 'B_CENTROID'

# .............................................................................
def get_line_count(filename):
    """ find total number lines in a file """
    cmd = "wc -l {}".format(repr(filename))
    info, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    temp = info.split(b'\n')[0]
    line_count = int(temp.split()[0])
    return line_count

# .............................................................................
def get_process_count():
    return cpu_count() - 2

# .............................................................................
def _find_chunk_files(big_csv_filename, out_csv_filename):
    """ Finds multiple smaller input csv files from a large input csv file, 
    if they exist, and return these filenames, paired with output filenames 
    for the results of processing these files. """
    cpus2use = get_process_count()
    in_base_filename, _ = os.path.splitext(big_csv_filename)
    # Construct provider filenames from outfilename and separate in/out paths
    out_fname_noext, ext = os.path.splitext(out_csv_filename)
    outpth, basename = os.path.split(out_fname_noext)
    out_base_filename = os.path.join(outpth, basename)
        
    total_lines = get_line_count(big_csv_filename) - 1
    chunk_size = int(total_lines / cpus2use)
    
    csv_filename_pairs = []
    start = 1
    stop = chunk_size
    while start <= total_lines:
        in_filename = '{}_chunk-{}-{}{}'.format(in_base_filename, start, stop, ext)
        out_filename =  '{}_chunk-{}-{}{}'.format(out_base_filename, start, stop, ext)
        if os.path.exists(in_filename):
            csv_filename_pairs.append((in_filename, out_filename))
        else:
            # Return basenames if files are not present
            csv_filename_pairs = [(in_base_filename, out_base_filename)]
            print('Missing file {}'.format(in_filename))
            break
        start = stop + 1
        stop = start + chunk_size - 1
    return csv_filename_pairs, chunk_size

# .............................................................................
def get_chunk_files(big_csv_filename, out_csv_filename):
    """ Creates multiple smaller input csv files from a large input csv file, and 
    return these filenames, paired with output filenames for the results of 
    processing these files. """
    csv_filename_pairs, chunk_size = _find_chunk_files(
        big_csv_filename, out_csv_filename)
    # First pair is existing files OR basenames
    if os.path.exists(csv_filename_pairs[0][0]):
        header = get_header(big_csv_filename)
        return csv_filename_pairs, header
    else:
        in_base_filename = csv_filename_pairs[0][0]
        out_base_filename = csv_filename_pairs[0][1]
    
    csv_filename_pairs = []
    try:
        bigf = open(big_csv_filename, 'r', encoding='utf-8')
        header = bigf.readline()
        line = bigf.readline()
        curr_recno = 1
        while line != '':
            # Reset vars for next chunk
            start = curr_recno
            stop = start + chunk_size - 1
            in_filename = '{}_chunk-{}-{}.csv'.format(in_base_filename, start, stop)
            out_filename =  '{}_chunk-{}-{}.csv'.format(out_base_filename, start, stop)
            csv_filename_pairs.append((in_filename, out_filename))
            try:
                # Start writing the smaller file
                inf = open(in_filename, 'w', encoding='utf-8')
                inf.write('{}'.format(header))
                while curr_recno <= stop:
                    if line != '':
                        inf.write('{}'.format(line))
                        line = bigf.readline()
                        curr_recno += 1
                    else:
                        curr_recno = stop + 1
            except Exception as inner_err:
                print('Failed in inner loop {}'.format(inner_err))
                raise
            finally:
                inf.close()
    except Exception as outer_err:
        print('Failed to do something {}'.format(outer_err))
        raise
    finally:
        bigf.close()
    
    return csv_filename_pairs, header

# .............................................................................
def get_header(filename):
    """ find fieldnames from the first line of a CSV file """
    header = None
    try:
        f = open(filename, 'r', encoding='utf-8')
        header = f.readline()
    except Exception as e:
        print('Failed to read first line of {}: {}'.format(filename, e))
    finally:
        f.close()
    return header

# .............................................................................
def get_csv_reader(datafile, delimiter, encoding, quote_char=csv.QUOTE_NONE):
    try:
        f = open(datafile, 'r', encoding=encoding) 
        reader = csv.reader(f, delimiter=delimiter, escapechar='\\', 
                            quoting=csv.QUOTE_NONE)
    except Exception as e:
        raise Exception('Failed to read or open {}, ({})'
                        .format(datafile, str(e)))
    else:
        print('Opened file {} for read'.format(datafile))
    return reader, f

# .............................................................................
def get_csv_writer(datafile, delimiter, encoding, fmode='w'):
    ''' Get a CSV writer that can handle encoding
    
    Args:
        datafile:
        delimiter:
        encoding:
        fmode:
    '''
    if fmode not in ('w', 'a'):
        raise Exception('File mode must be "w" (write) or "a" (append)')
    
    csv.field_size_limit(maxsize)
    try:
        f = open(datafile, fmode, encoding=encoding) 
        writer = csv.writer(
            f, escapechar='\\', delimiter=delimiter, quoting=csv.QUOTE_NONE)
    except Exception as e:
        raise Exception('Failed to read or open {}, ({})'
                        .format(datafile, str(e)))
    else:
        print('Opened file {} for write'.format(datafile))
    return writer, f

# .............................................................................
def get_csv_dict_reader(datafile, delimiter, encoding, fieldnames=None, 
                        quote_char=None):
    '''
    ignore_quotes: no special processing of quote characters
    '''
    try:
        f = open(datafile, 'r', encoding=encoding)
        if fieldnames is None:
            header = next(f)
            tmpflds = header.split(delimiter)
            fieldnames = [fld.strip() for fld in tmpflds]
        if quote_char is not None:
            dreader = csv.DictReader(
                f, fieldnames=fieldnames, quotechar=quote_char,
                escapechar='\\', restkey=EXTRA_VALS_KEY, delimiter=delimiter)
        else:
            dreader = csv.DictReader(
                f, fieldnames=fieldnames, quoting=csv.QUOTE_NONE,
                escapechar='\\', restkey=EXTRA_VALS_KEY, delimiter=delimiter)
            
    except Exception as e:
        raise Exception('Failed to read or open {}, ({})'
                        .format(datafile, str(e)))
    else:
        print('Opened file {} for dict read'.format(datafile))
    return dreader, f

# .............................................................................
def get_csv_dict_writer(datafile, delimiter, encoding, fldnames, fmode='w'):
    '''
    @summary: Get a CSV writer that can handle encoding
    '''
    if fmode not in ('w', 'a'):
        raise Exception('File mode must be "w" (write) or "a" (append)')
    
    csv.field_size_limit(maxsize)
    try:
        f = open(datafile, fmode, encoding=encoding) 
        writer = csv.DictWriter(f, fieldnames=fldnames, delimiter=delimiter,
                                escapechar='\\', quoting=csv.QUOTE_NONE)
    except Exception as e:
        raise Exception('Failed to read or open {}, ({})'
                        .format(datafile, str(e)))
    else:
        print('Opened file {} for dict write'.format(datafile))
    return writer, f


# ...............................................
def makerow(rec, outfields):
    row = []
    for fld in outfields:
        try:
            val = rec[fld]
            if val in (None, 'None'):
                row.append('')
            else:
                if isinstance(val, str) and val.startswith('\"'):
                    val = val.strip('\"')
                row.append(val)
        # Add output fields not present in record
        except:
            row.append('')
    return row


# ...............................................
def open_csv_files(infname, delimiter, encoding, ignore_quotes=True, 
                   infields=None, outfname=None, outfields=None, 
                   outdelimiter=None):
    ''' Open CSV data for reading as a dictionary (assumes a header), 
    new output file for writing (rows as a list, not dictionary)
    
    Args: 
        infname: Input CSV filename.  Either a sequence of filenames must 
            be provided as infields or the file must begin with a header
            to set dictionary keys. 
        delimiter: CSV delimiter for input and optionally output 
        encoding: Encoding for input and optionally output 
        ignore_quotes: if True, QUOTE_NONE
        infields: Optional ordered list of fieldnames, used when input file
            does not contain a header.
        outfname: Optional output CSV file 
        outdelimiter: Optional CSV delimiter for output if it differs from 
            input delimiter
        outfields: Optional ordered list of fieldnames for output header 
    '''
    # Open incomplete BISON CSV file as input
    csv_dict_reader, inf = get_csv_dict_reader(
        infname, delimiter, encoding, fieldnames=infields, 
        ignore_quotes=ignore_quotes)
    # Optional new BISON CSV output file
    csv_writer = outf = None
    if outfname:
        if outdelimiter is None:
            outdelimiter = delimiter
        csv_writer, outf = get_csv_writer(outfname, outdelimiter, encoding)
        # if outfields are not provided, no header
        if outfields:
            csv_writer.writerow(outfields)
    return (csv_dict_reader, inf, csv_writer, outf)
        

# ...............................................
def get_line(csvreader, recno):
    ''' Return a line while keeping track of the line number and errors
    
    Args:
        csvreader: a csv.reader object opened with a file
        recno: the current record number
    '''
    success = False
    line = None
    while not success and csvreader is not None:
        try:
            line = next(csvreader)
            if line:
                recno += 1
            success = True
        except OverflowError as e:
            recno += 1
            print( 'Overflow on record {}, line {} ({})'
                                 .format(recno, csvreader.line_num, str(e)))
        except StopIteration:
            print('EOF after record {}, line {}'
                                .format(recno, csvreader.line_num))
            success = True
        except Exception as e:
            recno += 1
            print('Bad record on record {}, line {} ({})'
                                .format(recno, csvreader.line_num, e))

    return line, recno


# ...............................................
if __name__ == '__main__':
    pth = '/tank/data/bison/2019/ancillary'
    
