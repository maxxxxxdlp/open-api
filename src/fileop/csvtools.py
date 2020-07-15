import csv
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
from sys import maxsize
import time

EXTRA_VALS_KEY = 'rest'
REQUIRED_FIELDS = []
CENTROID_FIELD = 'CENTROID'

# .............................................................................
def get_line_count(filename):
    """ find total number lines in a file """
    cmd = "wc -l {}".format(repr(filename))
    info, _ = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    temp = info.split(b'\n')[0]
    line_count = int(temp.split()[0])
    return line_count

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
def get_csv_reader(datafile, delimiter, encoding):
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
                        ignore_quotes=True):
    '''
    ignore_quotes: no special processing of quote characters
    '''
    try:
        f = open(datafile, 'r', encoding=encoding)
        if fieldnames is None:
            header = next(f)
            tmpflds = header.split(delimiter)
            fieldnames = [fld.strip() for fld in tmpflds]
        if ignore_quotes:
            dreader = csv.DictReader(
                f, fieldnames=fieldnames, quoting=csv.QUOTE_NONE,
                escapechar='\\', restkey=EXTRA_VALS_KEY, delimiter=delimiter)
        else:
            dreader = csv.DictReader(
                f, fieldnames=fieldnames, restkey=EXTRA_VALS_KEY, 
                escapechar='\\', delimiter=delimiter)
            
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
def getLine(csvreader, recno):
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
