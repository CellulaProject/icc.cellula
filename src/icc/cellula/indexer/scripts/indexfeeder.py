
from configparser import ConfigParser
from zope.configuration.xmlconfig import xmlconfig
from pkg_resources import resource_filename,resource_stream
from zope.component import getGlobalSiteManager, getUtility
from zope.interface import Interface
from icc.contentstorage.interfaces import IContentStorage
from icc.rdfservice.interfaces import IGraph
from icc.contentstorage import splitdigest
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
g=doc=getUtility(IGraph, name="doc")

def annotations(): # generator
    Q="""
    SELECT DISTINCT ?id
    WHERE {
     ?ann a oa:Annotation .
     ?ann oa:hasBody ?body .
     ?body nao:identifier ?id .
    }
    """
    qres=g.query(Q)
    for _id in qres:
        yield _id[0].toPython()

def bodies():
    i=1
    for key in annotations():
        lid, bid = splitdigest(key)
        content=storage.get(key).decode('utf8')
        content=content.replace("\t"," ").replace('"','""').replace("\n","\\n")
        yield (i, lid, bid, content)
        i+=1


def main():
    for row in bodies():
        i, lid, bid, body=row
        sys.stdout.write('%s\t%s\t%s\t"' % (i,lid,bid))
        sys.stdout.write(body)
        sys.stdout.write('"\n')

if __name__=="__main__":
    main()
