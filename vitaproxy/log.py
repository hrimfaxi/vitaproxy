#!/usr/bin/python2
# coding: utf-8

import logging, threading
from logging import DEBUG, INFO, WARNING, ERROR
from functools import wraps

from vitaproxy import constants
from vitaproxy.config import CONF

" 日志多线程锁 "
_msg_mtx = threading.Lock()

_filelog = None
toFile = None

def init_filelog():
    global _filelog, toFile
    _filelog = logging.getLogger(constants.PROG_NAME + "_filelogger")
    _filelog.setLevel(logging.INFO)
    fh = logging.FileHandler(CONF['log_filename'])
    _logger.info("Log filename: %s", CONF['log_filename'])
    fh.setLevel(logging.INFO)
    FORMAT = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
    fh.setFormatter(FORMAT)
    _filelog.handlers = []
    _filelog.addHandler(fh)
    toFile = use_mutex(_filelog.info)

def init_logger():
    logger = logging.getLogger(constants.PROG_NAME)

    level = logging.DEBUG
    if CONF['logLevel'] == 'debug':
        level = logging.DEBUG
    elif CONF['logLevel'] == 'error':
        level = logging.ERROR
    elif CONF['logLevel'] == 'warning':
        level = logging.WARNING
    elif CONF['logLevel'] == 'info':
        level = logging.INFO

    logger.setLevel(level)
    logger.handlers = []
    handler = logging.StreamHandler()
    FORMAT = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
    handler.setFormatter(FORMAT)
    logger.addHandler(handler)

    return logger

_logger = init_logger()

def use_mutex(fn):
    @wraps(fn)
    def callit(*args, **kwargs):
        with _msg_mtx:
            return fn(*args, **kwargs)
    return callit

debug, info, warning, error, setlevel = map(use_mutex, [
_logger.debug,
_logger.info,
_logger.warning,
_logger.error,
_logger.setLevel,
])

# vim: set tabstop=4 sw=4 expandtab:
