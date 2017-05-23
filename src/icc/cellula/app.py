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

package = __name__
ini_file = None
for arg in sys.argv:
    if arg.lower().endswith('.ini'):
        ini_file = arg
if ini_file == None:
    raise ValueError('.ini file not found')
#_config=resource_filename(package, ini_file) # FIXME how to determine?
_config = ini_file

config_utility = ConfigParser(
    defaults=os.environ, interpolation=ExtendedInterpolation())

config_utility.read(_config)
GSM = getSiteManager()
GSM.registerUtility(config_utility, Interface, name="configuration")

"""
from pyramid.request import Request
from pyramid.request import Response

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


def configuration(global_config, **settings):
    # config = Configurator(settings=settings,
    #     authentication_policy=getUtility(IAuthenticationPolicy, "authen_policy"),
    #     authorization_policy=getUtility(IAuthorizationPolicy,   "author_policy")
    # )
    # config.add_static_view('images', 'icc.cellula:static/images', cache_max_age=3600)
    # config.add_static_view('fonts', 'icc.cellula:static/fonts', cache_max_age=3600)
    # config.add_static_view('script', 'icc.cellula:static/script', cache_max_age=3600)
    # config.add_static_view('styles', 'icc.cellula:static/styles', cache_max_age=3600)
    # config.add_static_view('test', 'icc.cellula:static/test', cache_max_age=3600)
    # config.add_static_view('LTE', 'icc.cellula:static/AdminLTE', cache_max_age=3600)
    # config.include("cornice")

    config.load_zcml("configure.zcml")
    config.load_zcml("webapp.zcml")

    # config.include('icc.cellula.views')
    # config.include("icc.rdfservice.views")
    # ???? config.scan("icc.restfuldocs.views")

    # app=config.make_wsgi_app()

    # FIXME: Start queue upon "application ready" event !!! not here
    qeue = getUtility(IWorker, name="queue")
    qeue.start()
    # return app

if __name__ == "__main__":
    from waitress import serve
    import logging

    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)

    wsgiapp = main(None)
    serve(wsgiapp, host='::', port=8080)
