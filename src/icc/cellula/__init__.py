"""Main entry point
"""
from pyramid.config import Configurator

def main(global_config, **settings):
    config = Configurator(settings=settings)
    config.add_static_view('images', 'icc.cellula:static/images', cache_max_age=3600)
    config.add_static_view('fonts', 'icc.cellula:static/fonts', cache_max_age=3600)
    config.add_static_view('script', 'icc.cellula:static/script', cache_max_age=3600)
    config.add_static_view('styles', 'icc.cellula:static/styles', cache_max_age=3600)
    config.add_static_view('test', 'icc.cellula:static/test', cache_max_age=3600)
    config.include("cornice")
    config.include('pyramid_chameleon')
    config.include('icc.cellula.views')
    config.add_translation_dirs('icc.cellula:locales')
#    config.scan("icc.cellula.views")
#    config.include('pyramid_debugtoolbar')
#    config.scan("icc.rdfservice.views")
#    config.scan("icc.restfuldocs.views")
#    config.scan("icc.contentstorage.views")
    config.add_subscriber('icc.cellula.i18n.add_renderer_globals',
                          'pyramid.events.BeforeRender')
    config.add_subscriber('icc.cellula.i18n.add_localizer',
                          'pyramid.events.NewRequest')
    return config.make_wsgi_app()

if __name__=="__main__":
    from waitress import serve
    import logging

    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)

    wsgiapp=main(None)
    serve(wsgiapp, host='::', port=8080)
