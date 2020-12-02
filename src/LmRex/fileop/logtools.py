import logging
from logging.handlers import RotatingFileHandler
import os
import time

# Rough log of processing progress
LOGINTERVAL = 1000000
LOG_FORMAT = ' '.join(["%(asctime)s",
                       "%(funcName)s",
                       "line",
                       "%(lineno)d",
                       "%(levelname)-8s",
                       "%(message)s"])
LOG_DATE_FORMAT = '%d %b %Y %H:%M'
LOGFILE_MAX_BYTES = 52000000 
LOGFILE_BACKUP_COUNT = 5

class LMLog():
    # ...............................................
    def __init__(self, name, fname):
        self.log = self._get_logger(name, fname)
    
    # ...............................................
    def _get_logger(self, name, fname):
        log = logging.getLogger(name)
        log.setLevel(logging.DEBUG)
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        handlers = []
        handlers.append(RotatingFileHandler(fname, maxBytes=LOGFILE_MAX_BYTES, 
                                            backupCount=LOGFILE_BACKUP_COUNT))
        handlers.append(logging.StreamHandler())
        for fh in handlers:
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            log.addHandler(fh)
        return log
    
    # ...............................................
    def rotate_logfile(self, logpath, logname=None):
        if self.log is None:
            if logname is None:
                nm, _ = os.path.splitext(os.path.basename(__file__))
                logname = '{}.{}'.format(nm, int(time.time()))
            logfname = os.path.join(logpath, '{}.log'.format(logname))
            self.log = get_logger(logname, logfname)
        return log
    
# ...............................................
def log_info(msg, logger=None):
    if logger is None:
        print(msg)
    else:
        logger.log.info(msg)
    
# ...............................................
def log_warn(msg, logger=None):
    if logger is None:
        print(msg)
    else:
        logger.log.warn(msg)
    
# ...............................................
def log_error(msg, logger=None):
    if logger is None:
        print(msg)
    else:
        logger.log.error(msg)
    
# # .............................................................................
# def get_logger(name, fname):
#     log = logging.getLogger(name)
#     log.setLevel(logging.DEBUG)
#     formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
#     handlers = []
#     handlers.append(RotatingFileHandler(fname, maxBytes=LOGFILE_MAX_BYTES, 
#                                         backupCount=LOGFILE_BACKUP_COUNT))
#     handlers.append(logging.StreamHandler())
#     for fh in handlers:
#         fh.setLevel(logging.DEBUG)
#         fh.setFormatter(formatter)
#         log.addHandler(fh)
#     return log
# 
# # ...............................................
# def rotate_logfile(log, logpath, logname=None):
#     if log is None:
#         if logname is None:
#             nm, _ = os.path.splitext(os.path.basename(__file__))
#             logname = '{}.{}'.format(nm, int(time.time()))
#         logfname = os.path.join(logpath, '{}.log'.format(logname))
#         log = get_logger(logname, logfname)
#     return log

"""
{'Date': 'Mon, 30 Nov 2020 17:12:14 GMT', 
'Content-Type': 'application/json', 
'Access-Control-Allow-Origin': '*', 
'Access-Control-Allow-Methods': 'HEAD, GET, POST, DELETE, PUT, OPTIONS', 
'Server': 'Jetty(9.3.z-SNAPSHOT)', 
'Cache-Control': 'public, max-age=3601', 
'X-Varnish': '614072909', 
'Age': '0', 
'Via': '1.1 varnish (Varnish/6.0)', 
'Content-Length': '4986', 
'Connection': 'keep-alive'}
"""