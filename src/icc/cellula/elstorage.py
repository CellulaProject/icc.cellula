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
        refresh = refresh.lower() not in ["0", "", "off", "false"]
        self.refresh = refresh

    def put(self, features, id):
        self.engine.index(index=self.index,
                          doc_type=self.doctype,
                          id=id,
                          body=features,
                          refresh=self.refresh
                          )

    def get(self, id):
        return self.engine.get(index=self.index,
                               doc_type=self.doctype,
                               refresh=self.refresh,
                               id=id)

    def remove(self, id):
        return self.engine.delete(index=self.index,
                                  doc_type=self.doctype,
                                  refresh=self.refresh,
                                  id=id)

    def query(self, query):
        """Run query return list of corresponding
        document data."""
        hits = self.engine.search(index=self.index,
                                  doc_type=self.doctype,
                                  #body={"query": {"match_all": {}}}
                                  body={
                                      "query": {
                                          "simple_query_string": {
                                              "query": query,
                                              "analyzer": "snowball",
                                              # "fields": ["body^5","_all"],
                                              "default_operator": "and"
                                          }
                                      }
                                  }
                                  )
        return self.convert(hits)

    def convert(self, hits):
        total = hits["hits"]["total"]
        hits = [hit["_source"] for hit in hits["hits"]["hits"]]
        return total, hits

    def documents(self, min=None, max=None):
        """Return a "representative" list of documents, e.g.,
        for list table construction.
        """
        hits = self.engine.search(index=self.index,
                                  doc_type=self.doctype,
                                  body={
                                      "from": 0,
                                      "size": 20,
                                      "query": {"match_all": {}
                                                }
                                  }
                                  )

        return self.convert(hits)

    def refresh(self):
        return self.engine.refresh(index=self.index)


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
