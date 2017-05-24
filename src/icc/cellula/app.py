"""Main entry point
"""
from configparser import ConfigParser, ExtendedInterpolation
from zope.configuration.xmlconfig import xmlconfig
from pkg_resources import resource_filename, resource_stream
from zope.component import getSiteManager, getUtility
from zope.interface import Interface
from icc.cellula.interfaces import IWorker
from pyramid.interfaces import IAuthorizationPolicy, IAuthenticationPolicy
import sys
import os
import logging
logger = logging.getLogger("icc.cellula")

"""# FIXME: Make it configurable subscriber.
def request_factory(environ):
    request = Request(environ)
    if request.is_xhr:
        request.response = Response()
 #       request.response.headerlist = []
        request.response.headerlist.extend(
            (
                ('Access-Control-Allow-Origin', '*'),
#                ('Content-Type', 'application/json')
            )
        )
    return request

config.set_request_factory(request_factory)
"""


def configuration(config, **settings):
    config.load_zcml("configure.zcml")
    config.load_zcml("webapp.zcml")
