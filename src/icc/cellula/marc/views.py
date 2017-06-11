from isu.webapp import views
from icc.cellula import views as cviews
#from icc.cellula import view_config
from zope.i18nmessageid import MessageFactory
from .tasks import IssueDataTask
from zope.component import getUtility
from icc.cellula.interfaces import IRTMetadataIndex
import pprint

import logging

_ = _N = MessageFactory("isu.webapp")

logger = logging.getLogger('icc.cellula')


#@view_config(title=_("Import book data into MARC records"))
class View(views.View, cviews.View):
    """Defines view for MARC importer.
    """
    title = _("Import book data into MARC records")

    def action(self):
        req = self.request
        if req.method == "POST":
            post = req.POST
            logger.debug("Import: {}".format(pprint.pformat(post)))
            if "make10" in post or "makeall" in post:
                self.progress = _("Acquirement started.")
                logger.info("MARC: Acquirement started.")
                IssueDataTask().enqueue(block=False, view=self)
                return

            if "import" in post:
                self.progress = _("MARC import started.")
                logger.info("MARC: Import started.")
                return

    def answer(self):
        metadata = getUtility(IRTMetadataIndex, name="elastic")
        return metadata.query(variant="isbn")

    def result_table(self):
        return self()
