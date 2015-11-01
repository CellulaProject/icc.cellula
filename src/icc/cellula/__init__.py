"""Main entry point
"""
from configparser import ConfigParser
from zope.configuration.xmlconfig import xmlconfig
from pkg_resources import resource_filename,resource_stream
from zope.component import getGlobalSiteManager
from zope.interface import Interface
import sys,os

package=__name__
ini_file=None
for arg in sys.argv:
    if arg.lower().endswith('.ini'):
        ini_file=arg
if ini_file == None:
    raise ValueError('.ini file not found')
#_config=resource_filename(package, ini_file) # FIXME how to determine?
_config=ini_file
config_utility=ConfigParser()
config_utility.read(_config)
GSM=getGlobalSiteManager()
GSM.registerUtility(config_utility, Interface, name="configuration")

xmlconfig(resource_stream(package, "configure.zcml"))

from pyramid.config import Configurator
from pkg_resources import resource_stream, resource_string
from icc.cellula.interfaces import IApplication


def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_static_view('images', 'icc.cellula:static/images', cache_max_age=3600)
    config.add_static_view('fonts', 'icc.cellula:static/fonts', cache_max_age=3600)
    config.add_static_view('script', 'icc.cellula:static/script', cache_max_age=3600)
    config.add_static_view('styles', 'icc.cellula:static/styles', cache_max_age=3600)
    config.add_static_view('test', 'icc.cellula:static/test', cache_max_age=3600)
    config.include("cornice")
    config.include('pyramid_chameleon')

    config.add_translation_dirs('icc.cellula:locales')
    config.add_subscriber('icc.cellula.i18n.add_renderer_globals',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('icc.cellula.i18n.add_localizer',
                          'pyramid.events.NewRequest')


    config.include('icc.cellula.views')
#    config.include('pyramid_debugtoolbar')
#    config.scan("icc.rdfservice.views")
    config.scan("icc.restfuldocs.views")

    app=config.make_wsgi_app()
    GSM.registerUtility(app, IApplication, name='application')

    return app

if __name__=="__main__":
    from waitress import serve
    import logging

    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)

    wsgiapp=main(None)
    serve(wsgiapp, host='::', port=8080)
