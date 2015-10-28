""" Cornice services.
"""
from cornice import Service
from pyramid.response import Response
from pyramid.view import view_config
from pprint import pprint

class View(object):
    def __init__(self, *args, **kwargs):
        if args:
            self.request=args[1]
            self.traverse=args[0]
        else:
            self.request=kwargs.get('request', None)
            self.traverse=kwargs.get('traverse', None)
        _ = self.request.translate
        kw=kwargs
        self.title=kw.get('title', _('====TITLE====='))
        self.context=kw.get('context', kw.get('ob',None))

    @property
    def route_name(self):
        return self.request.matched_route.name

    @property
    def route_url(self):
        return self.request.route_url(self.route_name)

    def __call__(self):
        view={'view':self}
        if self.context != None:
            view['context']=self.context
        return view

    def active(self, name):
        mname=self.route_name
        if name==mname:
            return "active"
        raise ValueError('wrong route')

class ArchiveView(View):
    """View for archive
    """

    @property
    def body(self):
        _ = self.request.translate
        ts=_("Drag & Drop Files Here")
        return """
        <div id="dragandrophandler">%s</div>
        """ % ts

    @property
    def links(self):
        return """
        """

    @property
    def scripts(self):
        return """
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
        """

    @property
    def style(self):
        return """
        #dragandrophandler
{
border:2px dotted #0B85A1;
width:400px;
color:#92AAB0;
text-align:left;vertical-align:middle;
padding:10px 10px 10 10px;
margin-bottom:10px;
font-size:200%;
}
        """



@view_config(route_name='dashboard',renderer='templates/index.pt')
def get_dashboard(*args):
    request=args[1]
    _ = request.translate
    view=View(*args, title=_('Dashboard'))
    return view()

@view_config(route_name='archive',renderer='templates/index.pt')
def get_archive(*args):
    request=args[1]
    _ = request.translate
    view=ArchiveView(*args, title=_('Document Archive'))
    return view()

@view_config(route_name='email',renderer='templates/index.pt')
def get_email(*args):
    request=args[1]
    _ = request.translate
    view=View(*args, title=_("E-Mail"))
    return view()

def includeme(config):
    #config.scan("icc.cellula.views")
    config.scan()
    config.add_route('dashboard', "/")
    config.add_route('archive', "/archive")
    config.add_route('email', "/mail")
