from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from icc.cellula.interfaces import ISingletonTask
from icc.cellula.workers import Task
from zope.component import getUtility
from icc.cellula.interfaces import IRTMetadataIndex
import logging
logger = logging.getLogger('icc.cellula')

_ = _N = MessageFactory("isu.webapp")


@implementer(ISingletonTask)
class IssueDataTask(Task):

    def run(self):
        logger.info("Ran {}".format(self.__class__))
        metadata = getUtility(IRTMetadataIndex, "elastic")
        count, docs = metadata.query(variant="noisbn", count=10)
        logger.debug("Found {} documents".format(count))
        for doc in docs:
            logger.debug(doc["File-Name"])
            logger.debug(doc["mimetype"])
