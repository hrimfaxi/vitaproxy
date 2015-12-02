#!/usr/bin/python2
# coding: utf-8

import sys, os, optparse

from vitaproxy import constants
from vitaproxy import config
from vitaproxy.config import CONF
from vitaproxy import log
from vitaproxy import proxy_server

def parse_arguments(argv):
    parser = optparse.OptionParser(usage="%%prog %s" % ('[OPTION...] [PATH]'),
            description=('A proxy for PS3/PS4/PSV download PKG file'),
            add_help_option=True,
            )
    parser.add_option('-p', '--port', type='int', dest='port', action='store', default=CONF['port'],
            help=('Set HTTP Proxy server port'))
    parser.add_option('-c', '--cache', type='string', dest='cache', action='store', default=CONF['cache'],
            help=('Set VitaProxy cache list file'))
    parser.add_option('-d', '--download-dir', type='string', dest='downloadDIR', action='store', default=CONF['downloadDIR'],
            help=('Set VitaProxy download directory for automatically caching PKG/PUP file'))
    parser.add_option('-w', '--log-level', dest='logLevel', action='store', default=CONF['logLevel'],
                      choices = [ 'debug', 'info', 'warning', 'error' ], help=('Set verbose level'))

    opts, args = parser.parse_args(argv)
    opts = opts.__dict__
    for key in opts:
        if key in CONF:
            CONF[key] = opts[key]

def main():
    try:
        config.load_configure()
    except:
        config.save_configure()

    parse_arguments(sys.argv)

    log.init_logger()

    log.debug("Dumping configure")
    log.debug(CONF)
    log.info("Any clients will be served...")

    proxy_server.start_server()

# vim: set tabstop=4 sw=4 expandtab:
