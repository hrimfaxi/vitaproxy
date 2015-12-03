#!/usr/bin/python2
# coding: utf-8

" 安装脚本 "

import distutils.filelist
from vitaproxy import constants

try:
    import py2exe
except ImportError:
    pass

import setuptools, os.path

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setuptools.setup(
    entry_points = {
        'console_scripts' : [ 'vitaproxy= vitaproxy.main:main' ] },
    name = constants.PROG_NAME,
    version = constants.VERSION,
    author = "hrimfaxi",
    author_email = "outmatch@gmail.com",
    description = ("An http proxy server (with local cache support) for psvita/ps3/ps4"),
    license = "GPL",
    keywords = "proxy psvita ps4 ps3 server cache caching",
    url = "https://github.com/hrimfaxi/vitaproxy",
    packages = [ 'vitaproxy' ],
    long_description=read('README.txt')
)

# vim: set tabstop=4 sw=4 expandtab:
