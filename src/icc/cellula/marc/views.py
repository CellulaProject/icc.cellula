from isu.webapp import views
from icc.cellula import views as cviews
#from icc.cellula import view_config
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from icc.cellula.interfaces import ISingletonTask
from icc.cellula.workers import Task
from zope.component import getUtility
from icc.cellula.interfaces import IRTMetadataIndex

import logging

_ = _N = MessageFactory("isu.webapp")

logger = logging.getLogger('icc.cellula')


@implementer(ISingletonTask)
class IssueDataTask(Task):

    def run(self):
        logger.info("Ran {}".format(self.__class__))
        metadata = getUtility(IRTMetadataIndex, "elastic")
        count, docs = metadata.query(variant="noisbn", count=10)
        logger.debug("Found {} documents".format(count))


#@view_config(title=_("Import book data into MARC records"))


class View(views.View, cviews.View):
    """Defines view for MARC importer.
    """
    title = _("Import book data into MARC records")

    def action(self):
        if self.request.method == "POST":
            self.progress = "Acquirement started."
            IssueDataTask().enqueue(block=False, view=self)
        pass

    def answer(self):
        return []

    def result_table(self):
        return self()
