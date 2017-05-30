from __future__ import print_function
from zope.i18nmessageid import MessageFactory
from isu.enterprise.interfaces import IConfigurator
from icc.contentstorage.interfaces import IContentStorage
from zope.component import getUtility

_ = _N = MessageFactory("isu.webapp")


class view_config(object):
    __view_properties__ = {
        'title': _('====TITLE====='),
        # 'context':None, # a clash with add_wiew
    }

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __call__(self, wrapped):
        props = wrapped.__view_properties__ = {}
        for prop, default in self.__class__.__view_properties__.items():
            value = self.kwargs.pop(prop, default)
            props[prop] = value

        return wrapped


def default_storage():
    config = getUtility(IConfigurator, "configuration")
    storage_name = config["app:main"]["content_storage"]
    return getUtility(IContentStorage, storage_name)


def includeme(global_config, **settings):
    from .app import configuration
    return configuration(global_config, **settings)
