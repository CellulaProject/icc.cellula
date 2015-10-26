"""Main entry point
"""
from pyramid.config import Configurator

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.include("cornice")
    config.scan("icc.cellula.views")
#    config.scan("icc.rdfservice.views")
#    config.scan("icc.restfuldocs.views")
#    config.scan("icc.contentstorage.views")
    return config.make_wsgi_app()
