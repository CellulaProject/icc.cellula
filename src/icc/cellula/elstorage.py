from zope.interface import implementer
from .interfaces import IRTMetadataIndex
from isu.enterprise.interfaces import IConfigurator
from zope.component import getUtility
from elasticsearch import Elasticsearch


@implementer(IRTMetadataIndex)
class ElasticStorage(object):

    def __init__(self, url, index,
                 doctype="document",
                 refresh=True):
        self.url = url
        self.index = index
        self.engine = Elasticsearch([self.url])
        self.doctype = doctype
        self.refresh = refresh

    def put(self, features, id):
        self.engine.index(index=self.index,
                          doc_type=self.doctype,
                          id=id,
                          body=features,
                          refresh=self.refresh
                          )

    def remove(self, id):
        pass

    def query(self, query):
        """Run query return list of corresponding
        document data."""


class MetadataStorage(ElasticStorage):

    def __init__(self):
        # Use configurator
        conf = getUtility(IConfigurator, name="configuration")
        section = conf["elastic"]
        index = section.get("index", "metadata")
        doctype = section.get("doctype", "document")
        refresh = section.get("refresh", "True")  # FIXME: Convert to Boolean
        url = section.get("URL", "http://localhost:9200/")
        super(MetadataStorage, self).__init__(url=url,
                                              index=index,
                                              doctype=doctype,
                                              refresh=refresh)
