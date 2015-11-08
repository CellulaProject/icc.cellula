from icc.cellula.workers import Task, GetQueue

from icc.cellula.extractor.interfaces import IExtractor
from icc.cellula.indexer.interfaces import IIndexer
from icc.rdfservice.interfaces import IRDFStorage, IGraph
from icc.contentstorage.interfaces import IContentStorage
from icc.cellula.interfaces import ILock
from zope.component import getUtility
from zope.interface import implementer


class DocumentTask(Task):
    def __init__(self, content, headers):
        self.content=content
        self.headers=headers

class DocumentStoreTask(DocumentTask):
    """Store document to storage
    """
    priority=3

    def run(self):
        storage=getUtility(IContentStorage, name="content")
        lock=getUtility(ILock, name="content_lock")
        lock.acquire()
        storage.begin()
        nid_=storage.put(self.content)
        id_=self.headers.get('id',nid_)
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

        self.text_content=None
        if text_p:
            self.text_content=cont_data['text-body'].encode('utf-8')
            storage=getUtility(IContentStorage, name="content")
            ext_things['text-id']=storage.hash(self.text_content)
            ext_things['id']=ext_things['text-id']

        self.new_headers=ext_things

    def finalize(self):
        if self.text_content:
            self.enqueue(DocumentStoreTask(self.text_content, self.new_headers))
            #self.enqueue(IndexTask())
        self.enqueue(DocumentMetaStoreTask(self.new_headers))

class DocumentAcceptingTask(DocumentTask):
    def run(self):
        pass

    def finalize(self):
        self.enqueue(DocumentStoreTask(self.content, self.headers))
        self.enqueue(DocumentProcessingTask(self.content, self.headers))

class IndexTask(Task):
    """Task devoting to index content data
    """
    priority = 9
    processing = "thread"

    def __init__(self, index_name='annotation'):
        self.index_name=index_name

    def run(self):
        indexer=getUtility(IIndexer, "indexer")
        indexer.reindex(par=False, index=self.index_name)
