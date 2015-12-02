#!/usr/bin/python2
# coding: utf-8

import logging, threading
from logging import DEBUG, INFO, WARNING, ERROR
from functools import wraps

from vitaproxy import constants
from vitaproxy.config import CONF

" 日志多线程锁 "
_msg_mtx = threading.Lock()

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
