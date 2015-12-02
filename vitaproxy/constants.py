#!/usr/bin/python2
# coding: utf-8

import os.path, sys

""" 得到主目录: 使用了os.path.expanduser()函数 """
def get_home_directory():
    """On UNIX-like systems, this method will return the path of the home
    directory, e.g. /home/username. On Windows, it will return an MComix
    sub-directory of <Documents and Settings/Username>.
    """
    if sys.platform == 'win32':
        return os.path.join(os.path.expanduser('~'), 'MComix')
    else:
        return os.path.expanduser('~')

""" 得到配置目录 """
def get_config_directory():
    if sys.platform == 'win32':
        return get_home_directory()
    else:
        base_path = os.getenv('XDG_CONFIG_HOME',
            os.path.join(get_home_directory(), '.config'))
        return os.path.join(base_path, 'vitaproxy')

""" 得到数据目录 """
def get_data_directory():
    if sys.platform == 'win32':
        return get_home_directory()
    else:
        return os.path.join(get_home_directory(), "ps4")

SETTINGS_PATH = os.path.join(get_config_directory(), "settings.json")
CACHES_PATH = os.path.join(get_config_directory(), "cache.txt")
DOWNLOADDIR_PATH = get_data_directory()

PROG_NAME = "vitaproxy"
VERSION = "0.0.3"

# vim: set tabstop=4 sw=4 expandtab:
