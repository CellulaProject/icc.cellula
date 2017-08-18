from zope.interface import implementer
from .interfaces import IRTMetadataIndex
from isu.enterprise.interfaces import IConfigurator
from zope.component import getUtility
from elasticsearch import Elasticsearch, exceptions
import logging
logger = logging.getLogger('icc.cellula')


class Answer(list):
    """This is a list having
    additional attributes. So we can do
    self[hit_no] and
    self.total
    """

    def __str__(self):
        return "<{} count={}>".format(self.__class__.__name__, self.total)


@implementer(IRTMetadataIndex)
class ElasticStorage(object):

    def __init__(self, url, index,
                 doctype="document",
                 refresh=True,
                 timeouts=None):
        self.url = url
        self.index = index
        self.engine = Elasticsearch([self.url])
        self.doctype = doctype
        refresh = refresh.lower() not in ["0", "", "off", "false"]
        self.refresh = refresh
        if timeouts is None or not timeouts:
            timeouts = {
                "service": 60,
                "ui": 10
            }
        self.timeouts = timeouts

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

    def remove_index(self, index=None):
        """
        Removes index at all. Used for DEBUGGING and TESTING.
        """
        if index is None:
            index = self.index
        try:
            self.engine.indices.delete(index=index,
                                       # master_timeout=self.timeouts.get(
                                       #    "service", 30),
                                       # ignore_unavailable=True
                                       )
        except exceptions.NotFoundError:
            pass

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
            timeout = self.timeouts.get("service", 10)
        else:
            timeout = self.timeouts.get("ui", 30)
        if logger.isEnabledFor(logging.DEBUG):
            import pprint
            logger.debug("Query body :{}".format(pprint.pformat(body)))

        hits = self.engine.search(index=self.index,
                                  doc_type=self.doctype,
                                  body=body,
                                  request_timeout=timeout)
        return self.convert(hits, start=start, count=count)

    def convert(self, hits, start, count):
        total = hits["hits"]["total"]
        answer = Answer()
        answer.total = total
        [answer.append(hit["_source"]) for hit in hits["hits"]["hits"]]
        answer.start = start
        answer.total = total
        logger.debug("Answer: {}".format(answer))
        return answer

    def query_documents(self, body, min=None, max=None):
        """Return a "representative" list of documents, e.g.,
        for list table construction.
        """
        body["query"] = {"match_all": {}}
        return body

    def query_isbn(self, body):
        body["query"] = {
            "bool": {
                "must": {
                    "match_all": {}
                },

                "filter": {
                    "bool": {
                        "must": [
                            {
                                "exists": {
                                    "field": "isbn"
                                }
                            },
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
    __storage_name__ = "elastic"

    def __init__(self):
        # Use configurator
        conf = getUtility(IConfigurator, name="configuration")
        section = conf[self.__class__.__storage_name__]
        index = section.get("index", "metadata")
        doctype = section.get("doctype", "document")
        refresh = section.get("refresh", "True")  # FIXME: Convert to Boolean
        url = section.get("URL", "http://localhost:9200/")
        timeouts = {}
        for name in section.keys():
            if name.startswith("timeout."):
                k = name.split(".")[1]
                timeouts[k] = section.getint(name)
        logger.debug("Timeouts: {}".format(timeouts))
        super(MetadataStorage, self).__init__(url=url,
                                              index=index,
                                              doctype=doctype,
                                              refresh=refresh,
                                              timeouts=timeouts)


class MARCStorage(MetadataStorage):
    __storage_name__ = "marc"
