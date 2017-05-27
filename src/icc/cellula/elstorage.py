from zope.interface import implementer
from .interfaces import IRTMetadataIndex
from isu.enterprise.interfaces import IConfigurator
from zope.component import getUtility
from elasticsearch import Elasticsearch
import logging
logger = logging.getLogger('icc.cellula')


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

    def query(self, query=None, variant=None, count=20, start=0, **kwargs):
        """Run query return list of corresponding
        document data."""
        body = {
            "size": count,
            "from": start,
            "query": {
                "simple_query_string": {
                    "query": query,
                    "analyzer": "snowball",
                    # "fields": ["body^5","_all"],
                    "default_operator": "and"
                }
            }
        }

        if variant is not None and variant:
            method_name = "query_" + variant
            method = getattr(self, method_name)
            body = method(body, **kwargs)
        if logger.isEnabledFor(logging.DEBUG):
            import pprint
            logger.debug("Query body :{}".format(pprint.pformat(body)))

        hits = self.engine.search(index=self.index,
                                  doc_type=self.doctype,
                                  body=body
                                  )
        return self.convert(hits)

    def convert(self, hits):
        total = hits["hits"]["total"]
        hits = [hit["_source"] for hit in hits["hits"]["hits"]]
        return total, hits

    def query_documents(self, body, min=None, max=None):
        """Return a "representative" list of documents, e.g.,
        for list table construction.
        """
        body["query"] = {"match_all": {}}
        return body

    def query_noisbn(self, body):
        body["query"] = {
            "bool": {
                "must": {
                    "match_all": {}
                },

                "filter": {
                    "bool": {
                        "must_not": [
                            {
                                "exists": {
                                    "field": "isbn"
                                }
                            },
                            # ... < -- your other constraints, if any
                        ],
                        "must": [
                            {
                                "match": {
                                    "mimetype": "image/vnd.djvu"
                                }
                            }
                        ]
                    }
                }
            }
        }

        return body

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
