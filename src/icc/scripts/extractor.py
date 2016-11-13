#!/usr/bin/env python
from configparser import ConfigParser, ExtendedInterpolation
from zope.configuration.xmlconfig import xmlconfig
from pkg_resources import resource_filename, resource_stream
from zope.component import getGlobalSiteManager, getUtility
from zope.interface import Interface
from icc.cellula.extractor.interfaces import IExtractor
from icc.contentstorage.interfaces import IContentStorage
# from icc.rdfservice.interfaces import IGraph
from icc.contentstorage import splitdigest, hexdigest
import urllib.request
import sys
import os
import pprint

import logging
logger = logging.getLogger('icc.cellula')

package = __name__

ini_file = resource_filename("icc.cellula", "../../../icc.cellula.ini")

if ini_file is None:
    raise ValueError('.ini file not found')

_config = ini_file
config_utility = ConfigParser(
    defaults=os.environ, interpolation=ExtendedInterpolation())
config_utility.read(_config)
GSM = getGlobalSiteManager()
GSM.registerUtility(config_utility, Interface, name="configuration")

xmlconfig(resource_stream("icc.cellula", "extraction.zcml"))

EXTRACTOR_IDS = "extractor content recoll".split(" ")

extractors = [getUtility(IExtractor, name=name) for name in EXTRACTOR_IDS]

if __name__ == "__main__":
    print("Extractors are:", [ex.__class__.__name__ for ex in extractors])
    known = {}
    try:
        with open(sys.argv[1], "rb") as f:
            print("==== Extraction started ====")
            content = f.read()
            for ex in extractors:
                ex.debug = 100
                print("== Run extractor", ex.__class__.__name__)
                new = ex.extract(content, known)
                print("-- New:")
                pprint.pprint(new)
                known.update(new)
            print("==== Extraction finished ====")
            pprint.pprint(known)
    except IndexError:
        print("Usage\n./extractor.py <file>\n\n")
