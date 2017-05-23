from __future__ import print_function


def includeme(global_config, **settings):
    from .app import configurator
    return configuration(global_config, **settings)
