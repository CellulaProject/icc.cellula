from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from icc.cellula.interfaces import ISingletonTask
from icc.cellula.workers import Task
from icc.cellula.tasks import DocumentTask
from zope.component import getUtility
from icc.cellula.interfaces import IRTMetadataIndex, IWorker
from icc.cellula import default_storage
import pprint
from pymarc import rusmarcxml
from marcds.importer.issuerecog import DJVUtoMARC
import logging
import tempfile
from . import MIME_TYPE

logger = logging.getLogger('icc.cellula')

_ = _N = MessageFactory("isu.webapp")


@implementer(ISingletonTask)
class IssueDataTask(Task):

    def run(self):
        logger.info("Ran {}".format(self.__class__))
        metadata = getUtility(IRTMetadataIndex, "elastic")
        docs = metadata.query(variant="noisbn", count=1000)
        logger.debug("Found {} documents".format(docs.count))
        if docs.count == 0:
            logger.debug("No document for processing.")
            return
        storage = default_storage()
        queue_thread = getUtility(IWorker, name="queue")
        for doc in docs:
            logger.debug(doc["File-Name"])
            logger.debug(doc["mimetype"])
            id = doc["id"]
            content = storage.get(doc["id"])
            if isinstance(content, (str, bytes)):
                logger.debug("Content length: {}".format(len(content)))
                tmp = tempfile.NamedTemporaryFile(dir=queue_thread.tmpdir)
                tmp.write(content)
                tmp.flush()
            else:
                raise NotImplementedError("type is not supported")
            r = DJVUtoMARC(tmp.name)
            data = r.issue_data(noexc=True)
            if data is not None:
                logger.debug("Got some data ISBN {}".format(r.isbn))
                logger.debug("Lines: {}".format(r.lines))
            else:
                logger.debug("No data found.")
                continue
            # query isbn with isbnlib
            if r.isbn:
                rc = r.query_with_isbn(services=("wcat", "goob", "openl"))
            else:
                continue
            if rc:
                doc["isbn"] = r.isbn
            else:
                continue
            for k, fs in rc.items():
                if fs is None:
                    continue
                for fk, fv in fs.items():
                    fk = fk.lower()
                    doc[fk] = fv
                    logger.debug("{} = {}".format(fk, fv))
            metadata.put(doc, id)

            logger.debug(pprint.pformat(doc))
            logger.info(
                "Book {title} filename: {File-Name} stored!".format(doc))


class MARCStreamImportTask(Task):
    def __init__(self, stream, features=None,
                 *args, **kwargs):
        # FIXME: refactor headers -> features
        super(DocumentTask, self).__init__(*args, **kwargs)
        if features is None:
            features = {}
        features["mimetype"] = MIME_TYPE
        self.stream = stream
        self.features = features

    def run(self):
        self.records = rusmarcxml.parse_xml_to_array(self.stream)

    def finalize(self):
        if self.records:
            conf = getUtility(IConfigurator, "configuration")
            size = conf["marc"].getint("bunch_size", 10)
            MARCRecordsImportTask(records=self.records,
                                  count=size,
                                  features=self.features
                                  ).enqueue()


class MARCRecordsImportTask(Task):
    def __init__(self, records, count, features):
        self.records = records
        self.count = count
        self.features = features
        self.processed = []

    def run(self):
        # process
        count = self.count
        if count == 0:
            raise ValueError("zero-sized bunch")
        while True:
            if count <= 0:
                break
            if not self.records:
                break

            rec = self.records.pop()
            self.processed.append(rec)
            # processing
            logger.debug("Processing record: {}".format(str(rec)))
            connt -= 1

    def finalize(self):
        if len(self.processed) < self.count:
            # Something bad happened or all the records already processed
            return
        else:
            MARCRecordsImportTask(records=self.records,
                                  count=self.count,
                                  features=self.features)
