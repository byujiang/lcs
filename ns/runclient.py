#!/usr/local/bin/python3

import pdb
import logging
import threading
import os,sys,time
import struct
from tornado.httpclient import HTTPClient
from tornado.httpclient import AsyncHTTPClient
from tornado.concurrent import Future

CHUNKSIZE=80*1024*1024

logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                filename='/usr/spool/ns/client_log',
                filemode='a+')

def geturl_read(host,filepath,uid,gid,pos,size):
    url = "http://"+host+"/read?filepath="+filepath+"&uid="+uid+"&gid="+gid+"&pos="+str(pos)+"&size="+str(size)
    print(url)
    return url

def fetch(host,filepath,uid,gid,pos,size):
    url=geturl_read(host,filepath,uid,gid,pos,size)
    logging.debug(url)
    http_client=HTTPClient()
    response=http_client.fetch(url)
#    http_client=AsyncHTTPClient()
#    my_future =Future()
#    fetch_future=http_client.fetch(url)
#    fetch_future.add_done_callback(lambda f:myfuture.set_result(f.result()))
#    return my_future
    chunklen=len(response.body)-8
    posnew,chunknew = struct.unpack('l%ds'%chunklen,response.body)
    return posnew,chunknew

def writer(filepath, position, chunk):
    f=open(filepath,'rb+')
    f.seek(position)
    f.write(chunk)
    f.close()

def deal(host,filepath,targetdir,uid,gid,pos,streamsize):
    posnew,chunknew=fetch(host,filepath,uid,gid,pos,streamsize)
    writer(targetdir, posnew, chunknew)

def readentrance(host,filepath,targetdir,uid,gid,pos,size):
    start_time=time.time()
    logging.debug("start python module"+format(start_time)+"  POS: "+str(pos))
    if (int(size)<=CHUNKSIZE):
        streamsize=int(size)
        deal(host,filepath,targetdir,uid,gid,pos,streamsize)
    else:
        streamsize=CHUNKSIZE
        i=0
        streamnum=(int(size))//CHUNKSIZE
        while(i<streamnum):
            deal(host,filepath,targetdir,uid,gid,int(pos)+streamsize*i,streamsize)
            i=i+1
        if(streamnum*streamsize<int(size)):
            deal(host,filepath,targetdir,uid,gid,int(pos)+streamsize*streamnum,int(size)-streamsize*streamnum
)
'''
    else:
        threads=[]
        streamsize=CHUNKSIZE
        i=0
        streamnum=(int(size))//CHUNKSIZE
        while(i<streamnum):
            th=threading.Thread(target=deal, args=(host,filepath,targetdir,uid,gid,int(pos)+streamsize*i,streamsize))
            threads.append(th)
            i=i+1
        if(streamnum*streamsize<int(size)):
            th=threading.Thread(target=deal, args=(host,filepath,targetdir,uid,gid,int(pos)+streamsize*streamnum,int(size)-streamsize*streamnum))
            threads.append(th)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    end_time=time.time()
    logging.debug("ipd:"+str(os.getpid())+"exct_time:"+format(end_time-start_time))
#    chunk=chunknew.decode('utf-8')
#    return posnew,chunk
'''

if __name__=="__main__":
    readentrance("202.122.37.90:28001","/eos/user/c/chyd/5000","/tmp/log","0","0","0","5242880000")
#    pos=0
#    size=10*1024*1024
#    thread_list=[]
#    for i in range(1):
#        t=threading.Thread(target=readentrance, args=("202.122.37.90:28001","/eos/user/x/xuq/hosts","/cdfs_data/log","0","0",str(pos+i*size),str(size)))
#        thread_list.append(t)
#    for t in thread_list:
#        t.start()
#    for t in thread_list:
#        t.join()
