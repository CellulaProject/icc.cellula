from __future__ import print_function


def includeme(global_config, **settings):
    from .app import main
    return main(global_config, **settings)
