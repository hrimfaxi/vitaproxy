#!/usr/bin/python2
# coding: utf-8

import os, json, logging
from vitaproxy import constants

CONF = {
    'showSpeed': True,
    'fixVitaPath' : True,
    'expertMode' : False,
    'downloadDIR' : constants.DOWNLOADDIR_PATH,
    'updateInterval' : 2,
    'bufSize' : 1 * 1024 * 1024,
    'port' : 8080,
    'cache' : constants.CACHES_PATH,
    'logLevel' : logging.DEBUG,
    'httpsProxy' : '',
}

def load_configure():
    with open(constants.SETTINGS_PATH, "rb") as f:
        settings = json.load(f)
        for e in settings:
            if e in CONF:
                CONF[e] = settings[e]

def save_configure():
    try:
        os.mkdir(constants.get_config_directory())
    except OSError:
        pass
    with open(constants.SETTINGS_PATH, "wb") as f:
        json.dump(CONF, f, sort_keys=True, indent=4, separators=(',', ': '))

# vim: set tabstop=4 sw=4 expandtab:
