from icc.cellula.workers import Task, GetQueue

from icc.cellula.extractor.interfaces import IExtractor
from icc.cellula.indexer.interfaces import IIndexer
from icc.rdfservice.interfaces import IRDFStorage, IGraph
from icc.cellula.interfaces import ILock, ISingletonTask, IQueue, IWorker, IMailer
from zope.component import getUtility, queryUtility
from zope.interface import implementer, Interface
from string import Template
import time
import logging
from .interfaces import IRTMetadataIndex
from icc.cellula import default_storage
logger = logging.getLogger('icc.cellula')


class DocumentTask(Task):

    def __init__(self, content, headers):
        self.content = content
        self.headers = headers


class DocumentStoreTask(DocumentTask):
    """Store document to storage
    """
    priority = 3

    def __init__(self, content, headers, key='id'):
        """Store content under ['key'] id in the document storage.

        Arguments:
        - `content`:Content to store.
        - `headers`:a Dictionary containing [key] id.
        - `key`:name of Id.
        """
        DocumentTask.__init__(self, content, headers)
        self.key = key

    def run(self):

        storage = default_storage()
        lock = getUtility(ILock, name="content")
        lock.acquire()
        self.locks.append(lock)
        storage.begin()
        nid_ = storage.put(self.content, self.headers)
        id_ = self.headers.get(self.key, nid_)
        if id_ != nid_:
            storage.abort()
            self.locks.pop()
            lock.release()
            raise RuntimeError("ids differ %s:%s" % (id_, nid_))
        storage.commit()
        self.locks.pop()
        lock.release()
        return id_


class DocumentMetaStoreTask(DocumentTask):
    priority = 3

    def __init__(self, headers):
        self.headers = headers

    def run(self):
        doc_meta = getUtility(IRDFStorage, name='documents')
        lock = getUtility(ILock, name="documents")
        lock.acquire()
        self.locks.append(lock)
        rc = doc_meta.store(self.headers)
        self.locks.pop()
        lock.release()
        return rc


class DocumentProcessingTask(DocumentTask):
    priority = 8
    processing = "process"

    def run(self):

        self.text_content = None
        self.new_headers = {}
        things = self.headers

        extractor = getUtility(IExtractor, name='extractor')
        ext_data = extractor.extract(self.content, things)

        ext_things = {}
        ext_things.update(things)
        ext_things.update(ext_data)

        content_extractor = getUtility(IExtractor, name='content')
        cont_data = content_extractor.extract(self.content, ext_things)

        if 'text-body' not in cont_data:
            recoll_extractor = getUtility(IExtractor, name='recoll')
            ext_things.update(cont_data)
            cont_data = recoll_extractor.extract(self.content, ext_things)

        text_p = things['text-body-presence'] = 'text-body' in cont_data

        ext_things.update(cont_data)

        if text_p:
            self.text_content = cont_data['text-body'].encode('utf-8')
            storage = default_storage()
            ext_things['text-id'] = storage.hash(self.text_content)

        self.new_headers = ext_things

    def finalize(self):
        if self.text_content:
            self.enqueue(DocumentStoreTask(self.text_content,
                                           self.new_headers, key='text-id'))
            # self.enqueue(ContentIndexTask())
        self.enqueue(DocumentMetaStoreTask(self.new_headers))
        self.enqueue(DocumentElasticIndexTask(
            self.text_content, self.new_headers))
        # self.enqueue(MetaIndexTask())


class DocumentAcceptingTask(DocumentTask):

    def run(self):
        pass

    def finalize(self):
        self.enqueue(DocumentStoreTask(self.content, self.headers))
        self.enqueue(DocumentProcessingTask(self.content, self.headers))


class MetadataStorageQueryMixin(object):

    def sparql(self, **qp):  # qp=query_params as keywords
        graph = qp['graph']
        if self.__class__.query:
            doc_meta = getUtility(IRDFStorage, name=graph)
            q = Template(self.__class__.query).substitute(**qp)
            if 'LIMIT' in qp:
                q += " LIMIT {LIMIT}\n".format(**qp)
            if doc_meta is None:
                logger.error("Storage '{}' not found.".format(graph))
                return []
            return doc_meta.sparql(query=q)
        else:
            raise ValueError("No query supplied")

    def prolog_query(self, query, **qp):
        graph = qp['graph']
        q = Template(query).substitute(**qp)
        doc_meta = getUtility(IRDFStorage, name=graph)
        yield from doc_meta.query(query=q)


@implementer(ISingletonTask)
class MetadataRestoreTask(Task, MetadataStorageQueryMixin):
    """Tries to find documents without metadata
    (hasBody is absent). Get a number of them from
    storage and process again with DocumentProcessing
    task.
    """
    priority = 10
    processing = "thread"
    default_max_number = 2
    query = """
        SELECT DISTINCT ?id
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:hasTarget ?target .
           ?target nie:identifier ?id .
        FILTER NOT EXISTS { ?ann oa:hasBody ?body }
        }
    """

    def __init__(self, processed=0):
        """If processed>0 finally run indexer even
        if we did not found any documents.
        """

        Task.__init__(self)
        config = getUtility(Interface, "configuration")
        keys = config["maintainance"]["keys"]
        keys = (k.strip() for k in keys.split(","))
        if "metadata" in keys:
            self.max_number = config["maintainance_metadata"].get(
                "bunch", self.__class__.default_max_number)
        else:
            self.max_number = self.__class__.default_max_number
        self.max_number = int(self.max_number)
        self.doc_ids = []
        self.processed = processed

    def run(self):
        self.doc_ids = self.sparql(graph="documents", LIMIT=self.max_number)
        self.doc_ids = list(self.doc_ids)  # Must be a list, not a generator.

    def finalize(self):
        lids = 0
        for (doc_id,) in self.doc_ids:
            lids += 1
            self.enqueue(DocumentMetadataRestoreTask(doc_id))
        if lids >= self.max_number:
            # Process next bunch
            self.enqueue(MetadataRestoreTask(self.processed + lids))
            pass
        if lids + self.processed > 0:
            self.enqueue(ContentIndexTask())


class DocumentMetadataRestoreTask(Task, MetadataStorageQueryMixin):
    """Find a document by its id in the storage,
    load it, process it with a DocumentProcessingTask.
    """
    priority = 8
    processing = "thread"
    query = """
        SELECT DISTINCT ?mimeType ?fileName
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:hasTarget ?target .
           ?target nie:identifier "$targetId" .
           ?target nmo:mimeType ?mimeType .
           ?target nfo:fileName ?fileName .
        }
    """

    def __init__(self, doc_id):
        Task.__init__(self)
        self.doc_id = doc_id
        self.content = None
        self.headers = {}

    def run(self):
        headers = self.headers
        logger.info("Restoring ID='{}'".format(self.doc_id))
        rset = self.sparql(graph="documents", targetId=self.doc_id)
        for row in rset:
            mimeType, fileName = row
            headers["File-Name"] = fileName
            headers["Content-Type"] = mimeType
        headers["id"] = self.doc_id
        headers["restore-metadata"] = True
        logger.debug(headers)
        storage = default_storage()

        try:
            content = self.content = storage.get(self.doc_id)
        except KeyError:
            logger.error("Content key invalid! Removing meta for it.")
            for _ in self.prolog_query("icc:annotation_remove(target,'$tid')", graph="documents", tid=self.doc_id):
                logger.info("Removed document with id: {}".format(self.doc_id))

    def finalize(self):
        if self.content:
            self.enqueue(DocumentProcessingTask(self.content, self.headers))
        else:
            logger.error(
                "Document '{}' has metadata, but does not its content!".format(self.doc_id))
            # FIXME Document must be eliminated from matadatastorage


class DocumentElasticIndexTask(DocumentTask):
    priority = 20  # the lowest priority
    delay = 5  # sec
    processing = "thread"

    def run(self):
        id = self.headers["id"]
        logger.info(
            "------------- Content index task run ----------------------------")
        # logger.debug(self.content[:100])
        # logger.debug(self.headers.keys())
        estore = getUtility(IRTMetadataIndex, "elastic")
        estore.put(self.headers, id=id)


@implementer(ISingletonTask)
class ContentIndexTask(Task):
    """Task devoting to index content data
    """
    priority = 20  # lowest priority
    delay = 10   # sec
    processing = "thread"

    def __init__(self, index_name='annotation'):
        self.index_name = index_name
        self.lock = getUtility(ILock, 'indexing')

    def run(self):
        self.index_run = False
        tasks = GetQueue("tasks")
        pool = getUtility(IWorker, name="queue")
        #logger.debug ("Waiting")
        # time.sleep(self.delay)
        logger.debug("Checking conditions")
        nproc = pool.processing()
        # if nproc>=2:
        #     logger.debug ("Busy %d" % nproc)
        #     return
        self.index_run = True
        if not self.lock.acquire(False):
            return
        self.locks.append(self.lock)
        logger.debug("Run indexing")
        indexer = getUtility(IIndexer, "indexer")
        indexer.reindex(par=False, index=self.index_name)
        self.locks.pop()
        self.lock.release()

    def finalize(self):
        # Restart if indexing failed due to buzyness.
        if not self.index_run:
            logger.debug("Restart Indexing")
            time.sleep(self.delay)
            self.enqueue(ContentIndexTask())


class EmailSendTask(Task):
    # https://github.com/sendgrid/sendgrid-python

    def __init__(self,
                 message=None
                 ):

        Task.__init__(self)

        self.mailer = getUtility(IMailer, name="mailer")
        self.message = message

    def run(self):
        print("Action!")
        if self.message():
            self.mailer.send(self.message)
        else:
            debug.error("Couldn't send message {}".format(self.message))
