from icc.cellula.workers import Task, GetQueue

from icc.cellula.extractor.interfaces import IExtractor
from icc.cellula.indexer.interfaces import IIndexer
from icc.rdfservice.interfaces import IRDFStorage, IGraph
from icc.contentstorage.interfaces import IContentStorage
from icc.cellula.interfaces import ILock, ISingletonTask, IQueue, IWorker
from zope.component import getUtility
from zope.interface import implementer
import time
import logging
logger=logging.getLogger('icc.cellula')

class DocumentTask(Task):
    def __init__(self, content, headers):
        self.content=content
        self.headers=headers

class DocumentStoreTask(DocumentTask):
    """Store document to storage
    """
    priority=3

    def __init__(self, content, headers, key='id'):
        """Store content under ['key'] id in the document storage.

        Arguments:
        - `content`:Content to store.
        - `headers`:a Dictionary containing [key] id.
        - `key`:name of Id.
        """
        DocumentTask.__init__(self, content, headers)
        self.key=key

    def run(self):
        storage=getUtility(IContentStorage, name="content")
        lock=getUtility(ILock, name="content_lock")
        lock.acquire()
        storage.begin()
        nid_=storage.put(self.content, self.headers)
        id_=self.headers.get(self.key,nid_)
        if id_!=nid_:
            storage.abort()
            raise RuntimeError("ids differ %s:%s" % (id_,nid_))
        storage.commit()
        lock.release()
        return id_

class DocumentMetaStoreTask(DocumentTask):
    priority=3

    def __init__(self, headers):
        self.headers=headers
    def run(self):
        doc_meta = getUtility(IRDFStorage, name='documents')
        lock=getUtility(ILock, name="documents_lock")
        lock.acquire()
        rc=doc_meta.store(self.headers)
        lock.release()
        return rc

class DocumentProcessingTask(DocumentTask):
    priority=8
    processing="process"

    def run(self):
        self.text_content=None
        self.new_headers={}
        things=self.headers

        extractor=getUtility(IExtractor, name='extractor')
        ext_data=extractor.extract(self.content, things)

        ext_things={}
        ext_things.update(things)
        ext_things.update(ext_data)

        content_extractor=getUtility(IExtractor, name='content')
        cont_data=content_extractor.extract(self.content, ext_things)

        if not 'text-body' in cont_data:
            recoll_extractor=getUtility(IExtractor, name='recoll')
            ext_things.update(cont_data)
            cont_data=recoll_extractor.extract(self.content, ext_things)

        text_p=things['text-body-presence']='text-body' in cont_data

        ext_things.update(cont_data)

        if text_p:
            self.text_content=cont_data['text-body'].encode('utf-8')
            storage=getUtility(IContentStorage, name="content")
            ext_things['text-id']=storage.hash(self.text_content)

        self.new_headers=ext_things

    def finalize(self):
        if self.text_content:
            self.enqueue(DocumentStoreTask(self.text_content, self.new_headers, key='text-id'))
            self.enqueue(ContentIndexTask())
        self.enqueue(DocumentMetaStoreTask(self.new_headers))
        # self.enqueue(MetaIndexTask())

class DocumentAcceptingTask(DocumentTask):
    def run(self):
        pass

    def finalize(self):
        self.enqueue(DocumentStoreTask(self.content, self.headers))
        self.enqueue(DocumentProcessingTask(self.content, self.headers))


@implementer(ISingletonTask)
class ContentIndexTask(Task):
    """Task devoting to index content data
    """
    priority = 9 # lowest priority
    delay = 10   # sec
    processing = "thread"

    def __init__(self, index_name='annotation'):
        self.index_name=index_name

    def run(self):
        self.index_run=False
        tasks=GetQueue("tasks")
        pool=getUtility(IWorker, name="queue")
        logger.debug ("Waiting")
        time.sleep(self.delay)
        logger.debug ("Checking conditions")
        if tasks.full():
            logger.debug ("Queue full")
            return
        nproc=pool.processing()
        if nproc>=2:
            logger.debug ("Busy %d" % nproc)
            return
        self.index_run=True
        logger.debug ("Run indexing")
        indexer=getUtility(IIndexer, "indexer")
        indexer.reindex(par=False, index=self.index_name)

    def finalize(self):
        #Restart if indexing failed due to buzyness.
        if not self.index_run:
            logger.debug ("Restart Indexing")
            self.enqueue(ContentIndexTask())
