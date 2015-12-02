#!/usr/bin/python2
# coding: utf-8

import BaseHTTPServer, select, socket, SocketServer
import os.path, threading

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
        " 字典键为转化规则，值为转化的目标文件名 "
        self.replace_dict = {}
        self.load_cache_list(cache_list)

    def load_cache_list(self, fn):
        if not os.path.exists(fn):
            with open(fn, "w") as f:
                f.write("# format in cache.txt:\n\n")
                f.write("# replace_url->replace_file_path\n")
                f.write("# search:replace_filename->replace_file_path\n")
                f.write("# re:replace_url_regular_expression->replace_file_path\n\n")
                f.write("# if replace_file_path is relative then it will be lookup from download directory\n")
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
                        filename = url.split("?")[0].split("/")[-1]
                    if not fn:
                        continue

                    " fn如为相对路径名应加上下载目录路径 "
                    if not os.path.isabs(fn):
                        fn = os.path.join(CONF['downloadDIR'], fn)

                    try:
                        open(fn).close()
                        self.replace_dict[url] = fn
                    except IOError as e:
                        log.error("%s: %s", fn, str(e))

            log.info("%d local caches loaded" % (len(self.replace_dict)))
            log.debug("Dumping cache list:")
            log.debug(self.replace_dict)
        except IOError as e:
            log.error(str(e))

def start_server():
    server_address = ("0.0.0.0", CONF['port'])
    proxy_handler.ProxyHandler.protocol_version = "HTTP/1.1"
    run_event = threading.Event()

    httpd = ThreadingHTTPServer(server_address, proxy_handler.ProxyHandler, CONF['cache'])
    sa = httpd.socket.getsockname()
    log.info("Download directory: %s", CONF['downloadDIR'])
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
                log.error("Errno: %d - %s", e[0], e[1])
        except socket.error as e:
            if e.errno == 10054:
                log.error("Connection reset by peer")
            else:
                log.error(str(e))
    log.info("Server shutdown")

# vim: set tabstop=4 sw=4 expandtab:
