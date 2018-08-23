from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient
import tornado.ioloop
import tornado.web
import os,sys,re,time,struct,string
import threading
from tornado import gen
from functools import partial
import urllib.parse
import mimetypes
import math
import uuid
from concurrent.futures import ThreadPoolExecutor
import tornado.iostream
from tornado.escape import utf8
from tornado.log import gen_log
from ctypes import *
import logging

readchunky = False
total_downloaded = 0
threadpool = ThreadPoolExecutor(1)  # A thread for reading chunks from the file

DEBUG = False
res=0

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/usr/spool/ns/client_log',
                filemode='a+')

class Client:
    def _gen_boundary(self, file_size):
        if file_size < 1024:
            blen = 10
        else:
            blen = math.ceil(math.log(file_size, 2))
        bcnt = max(math.ceil(blen / 32), 1)
        logging.debug("filesize:  "+str(file_size)+"  bcnt:  "+str(bcnt)+"  uuid1:  "+str(uuid.uuid1()))
        return "".join([str(uuid.uuid1()).replace("-", "") for _ in range(bcnt)])
    def put_stream(self, url, pos, size, filename, on_response, chunk_size=1024):
        '''Uploads file to provided url.
        :param url: URL to PUT the file data to
        :param filename: Name of the file (Content-Disposition header)
        :param file_size: Size of the file in bytes. Used to produce a Content-Size header from file_size.
        :param on_response: See AsyncHTTPClient.fetch
        :return: Future content value under the provided url as binary string.
        '''
        uploadpos = pos        
        #file_size = os.path.getsize(filename)  # Be aware: this could also block! In production, you need to do this in a separated thread too!
        file_size = size  # Be aware: this could also block! In production, you need to do this in a separated thread too!

        logging.debug("filesize in put_stream is :"+str(file_size))
        ext = os.path.splitext(filename)[1].lower()
        if ext:
            content_type = mimetypes.types_map.get(ext, "application/octet-stream")
        else:
            content_type = "application/octet-stream"

        enc_filename = urllib.parse.quote(filename)
        boundary = self._gen_boundary(file_size)
        CRLF = '\r\n'
        post_head = b''.join(map(utf8, [
            '--', boundary, CRLF,
            # See https://tools.ietf.org/html/rfc5987 section 3.2.2 examples
            'Content-Disposition: form-data; name="file"; filename*=utf-8\'\'%s' % enc_filename, CRLF,
            'Content-Type: ', content_type, CRLF,
            'Content-Transfer-Encoding: binary', CRLF,
            CRLF,
        ]))
        post_tail = b''.join(map(utf8, [
            CRLF, '--', boundary, '--', CRLF
        ]))
        content_length = len(post_head) + int(file_size) + len(post_tail)
        headers = {
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Transfer-Encoding': 'binary',
            'Content-Length': str(content_length),
        }

        @gen.coroutine
        def body_producer(write):
            if DEBUG:
                sys.stdout.write(post_head.decode('ascii'))
            write(post_head)
            remaining = file_size
            with open(filename, "rb") as fileobj:
                fileobj.seek(int(uploadpos))
                while remaining > 0:
                  #  data = yield threadpool.submit(fileobj.read(int(remaining)), chunk_size)
                    data = fileobj.read(int(remaining))
                    if data:
                        remaining -= len(data)
                        logging.debug("len(data) in if is :"+str(len(data))+"uploadpos in while is :"+str(int(uploadpos))+"remaining in if is :"+str(len(data)))
                        if DEBUG:
                            sys.stdout.write(data.decode('utf-8'))
                        yield write(data)
                    else:
                        break
            if DEBUG:
                sys.stdout.write(post_tail.decode('ascii'))
            write(post_tail)
        
        request = tornado.httpclient.HTTPRequest(url=url, request_timeout=1200, method='POST', headers=headers,body_producer=body_producer)

        return tornado.httpclient.AsyncHTTPClient().fetch(request, callback=on_response)


def geturlupload(action,host,targetpath,pos,size,totalsize,uid,gid):
    if action=="upload":
        url = "http://"+host+"/upload?targetpath="+targetpath+"&pos="+str(pos)+"&size="+str(size)+"&totalsize="+str(totalsize)+"&uid="+uid+"&gid="+gid
        return url



@gen.coroutine
def upload(host,filepath,targetpath,pos,size,uid,gid,res):
    def on_response(request):
        global res
        logging.debug("=============== GOT RESPONSE ======")
        result=request.body.decode('ascii')
        logging.debug(result)
        logging.debug("===================================")
        if result.find('FT_OK')!=-1:
            res=0
        elif result.find('FT_EXIST')!=-1:
            res=1
        elif result.find('Permission denied')!=-1:
            res=2
        else:
            res=-1
        tornado.ioloop.IOLoop.current().stop() # Stop the loop when the upload is complete.

    client = Client()
    yield client.put_stream(geturlupload("upload",host,targetpath,pos,size,os.path.getsize(filepath),uid,gid), pos, size, filepath, on_response)



def uploadentrance(host,filepath,targetpath, uid, gid):
    start_time = time.time()
    filesize = os.path.getsize(filepath)
    upload(host, filepath, targetpath, 0, filesize, uid, gid, res)
    tornado.ioloop.IOLoop.instance().start()
    end_time = time.time()
    logging.debug("Total time :{}"+format(end_time-start_time))
    logging.debug("res-------------"+str(res))
    return res

if __name__=="__main__":
    uploadentrance("202.122.37.90:28003","Cns_touch_t.c","/root/leaf/test/Cns_touch_t.c","0", "0")
