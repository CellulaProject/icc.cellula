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

    # @property
    # def body(self):
    #     return "BODY"

    # def action(self):
    #     pass

    # def answer(self):
    #     return

    # def __call__(self):
    #     self.action()
    #     answer = self.answer()
    #     view = {'view': self}
    #     if answer != None:
    #         view['answer'] = answer
    #     # if self.context != None:
    #     #    view['context']=self.context
    #     # template
    #     # attrs
    #     self.request.response.headers['Access-Control-Allow-Origin'] = '*'
    #     return view
