"""Main entry point
"""
from zope.component import getUtility, getSiteManager
from .interfaces import IQueue, ILock, IWorker
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
    # config.hook_zca()

    config.load_zcml("configure.zcml")
    config.load_zcml("webapp.zcml")
