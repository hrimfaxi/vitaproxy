#!/usr/bin/python2
# coding: utf-8

import logging
from logging import DEBUG, INFO, WARNING, ERROR

from vitaproxy import constants
from vitaproxy.config import CONF

def init_logger():
    logger = logging.getLogger(constants.PROG_NAME)
    logger.setLevel(CONF['logLevel'])
    logger.handlers = []
    handler = logging.StreamHandler()
    FORMAT = logging.Formatter('%(asctime)-15s %(levelname)s: %(message)s')
    handler.setFormatter(FORMAT)
    logger.addHandler(handler)

    return logger

_logger = init_logger()

debug = _logger.debug
info = _logger.info
warning = _logger.warning
error = _logger.error
setLevel = _logger.setLevel

# vim: set tabstop=4 sw=4 expandtab:
