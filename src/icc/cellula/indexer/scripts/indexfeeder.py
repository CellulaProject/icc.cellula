
from configparser import ConfigParser
from zope.configuration.xmlconfig import xmlconfig
from pkg_resources import resource_filename,resource_stream
from zope.component import getGlobalSiteManager, getUtility
from zope.interface import Interface
from icc.contentstorage.interfaces import IContentStorage
#from icc.rdfservice.interfaces import IGraph
from icc.contentstorage import splitdigest, hexdigest
import urllib.request
import sys,os


package=__name__

ini_file=resource_filename("icc.cellula","../../../icc.cellula.ini")

if ini_file == None:
    raise ValueError('.ini file not found')

_config=ini_file
config_utility=ConfigParser()
config_utility.read(_config)
GSM=getGlobalSiteManager()
GSM.registerUtility(config_utility, Interface, name="configuration")

xmlconfig(resource_stream("icc.cellula", "indexfeeder.zcml"))

storage=getUtility(IContentStorage, name="content")
#g=doc=getUtility(IGraph, name="doc")

def annotations(): # generator
    config=getUtility(Interface, name="configuration")
    cf=config['indexfeeder']
    host=cf.get('host', '127.0.0.1')
    port=int(cf.get('port', '8080'))
    api=cf.get('api', '/api-fields')
    with urllib.request.urlopen('http://%s:%s%s/documents' % (host,port,api)) as f:
        for l in f:
            yield l.strip()

def bodies():
    i=1
    for key in annotations():
        key=key.decode('utf-8')  # !!! NOTE Sent as hexdigest, but received as bytes, must be decoded.
        try:
            content=storage.get(key)
        except ValueError:
            continue
        if content == None: # Due to a bug, e.g.
            continue
        content=content.replace(b"\t",b" ").replace(b'"',b'""').replace(b"\n",b"\\n").replace(b"\000",b" ").replace(b"\x0d",b" ")
        content=content.decode('utf8')
        yield (i, key, content)
        i+=1


def main():
    for row in bodies():
        i, hid, body=row
        if True:
            sys.stdout.write('%s\t%s\t' % (i,hid))
            sys.stdout.write('"')
            sys.stdout.write(body)
            sys.stdout.write('"')
            sys.stdout.write('\n')
        # else:
        #     sys.stdout.write('%s\t%s\t' % (i,hid))
        #     sys.stdout.write('"')
        #     # sys.stdout.write(body[:118160])
        #     sys.stdout.write(body[:118176])
        #     sys.stdout.write('"')
        #     sys.stdout.write('\n')

if __name__=="__main__":
    main()
