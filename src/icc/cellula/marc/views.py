from isu.webapp import views
from icc.cellula import views as cviews
from icc.cellula import view_config
from zope.i18nmessageid import MessageFactory

_ = _N = MessageFactory("isu.webapp")


#@view_config(title=_("Import book data into MARC records"))
class View(views.View, cviews.View):
    """Defines view for MARC importer.
    """
    title = _("Import book data into MARC records")

    def action(self):
        pass

    def answer(self):
        return [
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            },
            {
                "File-Name": "qweqwe.pdf",
                "title": "Title qwewqe",
                "id": "293581304534 34534",
                "ISBN": "90123-123",
                "author": "sdd"
            }
        ]

    progress = "Made 3 books..."

    def result_table(self):
        return self()
