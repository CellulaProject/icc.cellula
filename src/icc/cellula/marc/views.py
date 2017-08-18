from isu.webapp import views
from icc.cellula import views as cviews
# from icc.cellula import view_config
from zope.i18nmessageid import MessageFactory
from .tasks import IssueDataTask, MARCStreamImportTask
from zope.component import getUtility, queryUtility
from icc.cellula.interfaces import IRTMetadataIndex
import pprint
from icc.cellula import default_storage

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
                fileslist = post.getall('files')
                logger.debug("MARC: Files listing: {}".format(fileslist))
                for f in fileslist:
                    MARCStreamImportTask(stream=f.file).enqueue(
                        block=False, view=self)
                logger.info("MARC: Import started.")
                return
        if req.method == "GET":
            marc_indexer = queryUtility(IRTMetadataIndex, "marc")
            if marc_indexer is None:
                return
            get = req.GET
            id = get.get("marc_id", None)
            if id is None:
                return
            else:
                storage = default_storage()
                marc = storage.get(id=id)
                logger.debug("MARC:GET: {}:{}".format(id, marc))

    def answer(self):
        metadata = getUtility(IRTMetadataIndex, name="elastic")
        try:
            return metadata.query(variant="isbn")
        except Exception as e:
            return repr(e)

    def result_table(self):
        return self()
