#!/usr/bin/python2
# coding: utf-8

import BaseHTTPServer, select, socket, urlparse
import time, datetime, sys, os
import threading, ftplib, re

from vitaproxy import constants
from vitaproxy import config
from vitaproxy.config import CONF
from vitaproxy import log

fallocate = None
try:
    import fallocate
except ImportError as e:
    pass

sendfile = None
try:
    from sendfile import sendfile
except ImportError as e:
    pass

class RangeError(RuntimeError):
    pass

class ProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    __base = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle = __base.handle

    server_version = "Apache"
    rbufsize = 0                        # self.rfile Be unbuffered
    def handle(self):
        (ip, port) =  self.client_address
        if hasattr(self, 'allowed_clients') and ip not in self.allowed_clients:
            self.raw_requestline = self.rfile.readline()
            if self.parse_request(): self.send_error(403)
        else:
            self.__base_handle()

    def _connect_to(self, netloc, soc):
        i = netloc.find(':')
        if i >= 0:
            host_port = netloc[:i], int(netloc[i+1:])
        else:
            host_port = netloc, 80
        try: soc.connect(host_port)
        except socket.error, arg:
            try: msg = arg[1]
            except: msg = arg
            self.send_error(503, msg)
            return 0
        return 1

    def _connect_to_proxy(self, proxy, netloc, soc):
        if proxy.startswith("http://"):
            proxy = proxy[len("http://"):]
        host_port = proxy.split(':')
        host_port = (host_port[0], int(host_port[1]))
        try:
            soc.connect(host_port)
            soc.send("%s %s %s\r\n" % (self.command, netloc, self.request_version))
            self.headers['Connection'] = 'close'
            del self.headers['Proxy-Connection']
            for key_val in self.headers.items():
                soc.send("%s: %s\r\n" % key_val)
            soc.send("\r\n")
        except socket.error, arg:
            try: msg = arg[1]
            except: msg = arg
            self.send_error(503, msg)
            return 0
        return 1

    def fixPSVBrokenPath(self):
        if not CONF['fixVitaPath']:
            return

        last_http = self.path.rfind("http://")

        if last_http != 0 and last_http != -1:
            fixed = self.path[last_http:]
            log.info("Fixed psvita broken path %s to %s", self.path, fixed)
            self.path = fixed

    def do_CONNECT(self):
        log.info("CONNECT %s", self.path)
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            if CONF['httpsProxy']:
                if self._connect_to_proxy(CONF['httpsProxy'], self.path, soc):
                    self._read_write(soc, 300)
            else:
                if self._connect_to(self.path, soc):
                    self.send_response(200, "OK")
                    self.end_headers()
                    self._read_write(soc, 300)
        finally:
            soc.close()
            self.connection.close()

    def getFileLength(self, fn):
        return os.stat(fn).st_size

    """
              0-499     specifies the first 500 bytes
              500-999   specifies the second 500 bytes
              -500      specifies the last 500 bytes
              9500-     specifies the bytes from offset 9500 and forward
              0-0,-1    specifies the first and last byte only(*)(H)
              500-700,600-799
                        specifies 300 bytes from offset 500(H)
              100-199,500-599
                        specifies two separate 100-byte ranges(*)(H)
    """
    def getFileRange(self, replace_fn, range_str, file_length):
        if not range_str.startswith("bytes="):
            raise RangeError

        range_str = range_str[len("bytes="):]

        if not "-" in range_str:
            raise RangeError

        # multipart range not supported
        if "," in range_str:
            raise RangeError

        try:
            if range_str.startswith('-'):
                range_s_end = range_str.split('-')[-1]
                if file_length < int(range_s_end):
                    raise RangeError
                return file_length - int(range_s_end), file_length - 1

            range_s_start, range_s_end = range_str.split('-')
            range_start = int(range_s_start)

            if range_s_end:
                range_end = int(range_s_end)
            else:
                range_end = file_length - 1
        except ValueError as e:
            raise RangeError

        if range_start > range_end:
            raise RangeError

        return range_start, range_end

    def getLocalCache(self, replace_fn, head_only):
        log.info("cache redirected from %s to %s", self.path, replace_fn)
        log.debug("Dumping client headers:")
        for h in self.headers:
                log.debug("    %s: %s", h, self.headers[h])
        try:
            file_length = self.getFileLength(replace_fn)
            log.debug("file length: %d bytes", file_length)
            start, end = 0, file_length - 1
            lastModString = os.path.getmtime(replace_fn)
            lastModString = datetime.datetime.utcfromtimestamp(lastModString)
            lastModString = lastModString.strftime('%a, %d %b %Y %H:%M:%S GMT')
            dateString = os.path.getctime(replace_fn)
            dateString = datetime.datetime.utcfromtimestamp(dateString)
            dateString = dateString.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except IOError as e:
            self.send_error(500, "Internal Server Error")
            return

        if 'Range' in self.headers:
            try:
                " 在http协议中，start和end为[start, end] 范围从0开始到文件大小-1 "
                start, end = self.getFileRange(replace_fn, self.headers['Range'], file_length)
            except RangeError as e:
                """ rfc2616:  A server sending a response with status code 416
                (Requested range not satisfiable) SHOULD include a Content-Range
                field with a byte-range- resp-spec of "*".
                The instance-length specifies the current length of the selected resource. """
                self.send_response(416, 'Requested Range Not Satisfiable')
                self.send_header("Content-Range", "bytes */%d" % (file_length))
                return

            self.send_response(206, "Partial Content")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, file_length))
        else:
            self.send_response(200, "OK")

        content_length = end - start + 1
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", "%d" % (content_length))
        self.send_header("Connection", "close")
        self.send_header("Last-Modified", lastModString)
        self.send_header("Date", dateString)
        self.end_headers()

        if head_only:
            return

        log.debug("Range: from %u to %d", start, end)

        with open(replace_fn, "rb") as fd:
            if fallocate:
                log.debug("posix_fadvise: start from %d bytes, %d bytes length", start, content_length)
                fallocate.posix_fadvise(fd, start, content_length, fallocate.POSIX_FADV_SEQUENTIAL | fallocate.POSIX_FADV_WILLNEED)
            self._file_read_write(fd, start, end)

    def isPKGorPUPFile(self, path):
        localpath = os.path.basename(path).split('?')[0]
        ext = os.path.splitext(localpath)[-1].upper()
        if ".PKG" == ext:
            return True
        if ".PUP" == ext:
            return True
        return False

    def tryDownloadPath(self, path, head_only):
        if self.isPKGorPUPFile(path):
            localpath = os.path.join(CONF['downloadDIR'], os.path.basename(path).split('?')[0])
            if os.path.exists(localpath):
                self.getLocalCache(localpath, head_only)
                return True
        return False

    def do_GET(self, head_only=False):
        self.close_connection = 1
        self.fixPSVBrokenPath()

        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(self.path, 'http')

        if not path:
            path = '/'

        if scm not in ('http', 'ftp') or fragment or not netloc:
            self.send_error(400, "bad url %s" % self.path)
            return

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            if self.tryDownloadPath(self.path, head_only):
                return
            for url, filename in self.server.replace_dict.iteritems():
                if url.startswith('re:'):
                    r = re.compile(url[len('re:'):])

                    if r.match(self.path):
                        replace_url = self.path
                        self.getLocalCache(filename, head_only)
                        return

                if url.startswith('search:') and url[len('search:'):] in self.path:
                    self.getLocalCache(filename, head_only)
                    return

                if url == self.path:
                    self.getLocalCache(filename, head_only)
                    return

            if scm == 'http':
                if self._connect_to(netloc, soc):
                    soc.send("%s %s %s\r\n" % (self.command,
                                               urlparse.urlunparse(('', '', path,
                                                                    params, query,
                                                                    '')),
                                               self.request_version))
                    self.headers['Connection'] = 'close'
                    del self.headers['Proxy-Connection']
                    for key_val in self.headers.items():
                        soc.send("%s: %s\r\n" % key_val)
                    soc.send("\r\n")
                    self._read_write(soc)
            elif scm == 'ftp':
                # fish out user and password information
                i = netloc.find ('@')
                if i >= 0:
                    login_info, netloc = netloc[:i], netloc[i+1:]
                    try: user, passwd = login_info.split (':', 1)
                    except ValueError: user, passwd = "anonymous", None
                else: user, passwd ="anonymous", None

                try:
                    ftp = ftplib.FTP (netloc)
                    ftp.login (user, passwd)
                    if self.command == "GET":
                        ftp.retrbinary ("RETR %s"%path, self.connection.send)
                    ftp.quit ()
                except Exception, e:
                    log.error("FTP Exception, reason: %s", str(e))
        finally:
            soc.close()
            self.connection.close()

    def _file_read_write(self, fd, start, end):
        offset = start
        content_length = end - start + 1

        if CONF['showSpeed']:
            tm_a = [time.time(), offset - start]
            tm_b = [time.time(), offset - start]

        fd.seek(offset)
        try:
            while content_length > 0:
                if sendfile:
                    sent = sendfile(self.connection.fileno(), fd.fileno(), offset,
                            min(content_length, CONF['bufSize']))
                    if sent <= 0:
                        break
                else:
                    data = fd.read(min(content_length, CONF['bufSize']))
                    if not data:
                        break

                    self.connection.send(data)
                    sent = len(data)

                offset += sent
                content_length -= sent

                if CONF['showSpeed']:
                    tm_b = [time.time(), offset - start]
                    delta = tm_b[0] - tm_a[0]
                    rest = end - offset + 1

                    if delta >= CONF['updateInterval'] or rest == 0:
                        speed = (tm_b[1] - tm_a[1]) / delta
                        log.info("Speed: %.2fKB/S, Transfered: %d bytes, Remaining: %d bytes, ETA %d seconds"
                                 % (speed / 1000, offset - start, rest, rest / speed))
                        tm_a = tm_b
        except (OSError, socket.error) as e:
            log.error("Connection dropped, %d bytes sent, reason: %s", offset - start, str(e))

    def _read_write(self, soc, max_idling=20, local=False):
        iw = [self.connection, soc]
        local_data = ""
        ow = []
        count = 0
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 1)
            if exs: break
            if ins:
                for i in ins:
                    if i is soc: out = self.connection
                    else: out = soc
                    data = i.recv(CONF['bufSize'])
                    if data:
                        if local: local_data += data
                        else: out.send(data)
                        count = 0
            if count == max_idling: break
        if local: return local_data
        return None

    def do_HEAD(self):
        return self.do_GET(True)

    do_POST = do_GET
    do_PUT  = do_GET
    do_DELETE=do_GET

    base = BaseHTTPServer.BaseHTTPRequestHandler

    def send_header(self, keyword, value):
        log.debug("    %s: %s", keyword, value)
        ProxyHandler.base.send_header(self, keyword, value)

    def log_message(self, format, *args):
        log.info(format, *args)

# vim: set tabstop=4 sw=4 expandtab:
