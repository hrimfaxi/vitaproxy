#!/usr/bin/python2
# coding: utf-8

import BaseHTTPServer, select, socket, SocketServer
import threading

from types import FrameType, CodeType
from time import sleep

from vitaproxy import constants
from vitaproxy import config
from vitaproxy.config import CONF
from vitaproxy import log
from vitaproxy import proxy_handler

class ThreadingHTTPServer (SocketServer.ThreadingMixIn,
                           BaseHTTPServer.HTTPServer):
    def __init__ (self, server_address, RequestHandlerClass, cache_list = "cache.txt"):
        BaseHTTPServer.HTTPServer.__init__ (self, server_address,
                                            RequestHandlerClass)
        self.replace_list = []
        self.load_cache_list(cache_list)

    def load_cache_list(self, fn):
        try:
            with open(fn, "r") as f:
                for l in f:
                    l = l.decode(errors='ignore').strip()

                    if not l or l[0] == '#':
                        continue

                    if '->' in l:
                        url, fn = l.split('->')
                    else:
                        url = l

                        if url.rfind('?') > url.rfind('/'):
                            fn = url[url.rfind('/')+1:url.rfind('?')]
                        else:
                            fn = url[url.rfind('/')+1:]

                    if not fn:
                        continue

                    try:
                        open(fn).close()
                        self.replace_list.append([url, fn])
                    except IOError as e:
                        pass

            log.info("%d local caches loaded" % (len(self.replace_list)))
        except IOError as e:
            pass

def start_server():
    server_address = ("0.0.0.0", CONF['port'])
    proxy_handler.ProxyHandler.protocol_version = "HTTP/1.1"
    run_event = threading.Event()

    httpd = ThreadingHTTPServer(server_address, proxy_handler.ProxyHandler, CONF['cache'])
    sa = httpd.socket.getsockname()
    log.info("Servering HTTP on %s %s %s", sa[0], "port", sa[1])
    req_count = 0

    while not run_event.isSet():
        try:
            httpd.handle_request()
            req_count += 1
            if req_count == 1000:
                log.info("Number of active threads: %s", threading.activeCount())
                req_count = 0
        except select.error, e:
            if e[0] == 4 and run_event.isSet(): pass
            else:
                log.critical("Errno: %d - %s", e[0], e[1])
        except socket.error as e:
            if e.errno == 10054:
                log.error("Connection reset by peer")
            else:
                log.error(str(e))
    log.info("Server shutdown")

# vim: set tabstop=4 sw=4 expandtab:
