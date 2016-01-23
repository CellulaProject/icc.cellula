""" Cornice services.
"""
from cornice import Service
from pyramid.response import Response, FileResponse
import pyramid.view
from pprint import pprint, pformat
from icc.contentstorage.interfaces import IContentStorage
from icc.contentstorage import hexdigest
from zope.component import getUtility, queryUtility

from icc.rdfservice.interfaces import IRDFStorage, IGraph
from icc.cellula.indexer.interfaces import IIndexer

from rdflib import Literal
from pyparsing import ParseException
import tempfile
import datetime
from string import Template

from icc.cellula.auth import *

from pyramid.security import Allow
from pyramid.security import Everyone, Authenticated

import cgi
from icc.cellula.tasks import DocumentAcceptingTask, GetQueue, ContentIndexTask, MetadataRestoreTask
import logging
logger=logging.getLogger('icc.cellula')

DATE_TIME_FORMAT="%Y-%m-%dT%H:%M:%SZ"
DATE_TIME_FORMAT_IN="%Y-%m-%d %H:%M:%S%z"

def _(x):
    return x

class view_config(pyramid.view.view_config):
    __view_properties__= {
        'title':_('====TITLE====='),
        # 'context':None, # a clash with add_wiew
        }
    def __call__(self, wrapped):
        props=wrapped.__view_properties__={}
        for prop, default in self.__class__.__view_properties__.items():
            value=self.__dict__.pop(prop, default)
            props[prop]=value

        return pyramid.view.view_config.__call__(self,wrapped)

class View(object):
    __view_properties__={}
    scripts=[
        ('javascript', 'jquery-1.9.0.js'), # FIXME .min.
        ('javascript', 'pengines.js'),
        ('javascript', 'jquery-migrate-1.0.0.js'),
        ('javascript', 'dust-full-1.0.0.js'), # FIXME .min.
        ('javascript', 'goog.math.Long.js'),
        ('javascript', 'js-murmur3-128-1.0.0.js'),
        ('javascript', 'async-templating.js')
    ]
    panel_routes=[
        ('dashboard',_('Dashboard'), 'fa-dashboard'),
        ('archive',_('Archive'), 'fa-database'),
        ('metal_test',_('Metal'), 'fa-table'),
        ('maintain',_('Maintain'), 'fa-cogs'),
        ('debug_graph',_('Debug'), 'fa-wrench'),
        ]

    def __init__(self, *args, **kwargs):
        _vp=self.__class__.__view_properties__

        if args:
            self.traverse=args[0]
            self.request=args[1]
        else:
            self.request=kwargs.get('request', None)
            self.traverse=kwargs.get('traverse', None)
        _ = _T = self.request.translate
        self._=_
        kw=kwargs
        #self.context=kw.get('context', kw.get('ob',None))
        self.title=_T(kw.get('title', _vp.get('title')))
        self.exception=None

    @property
    def route_name(self):
        return self.request.matched_route.name

    def set_property(self, prop, value):
        return self.setattr(prop, value)

    @property
    def panel_items(self):
        """Return a generator for panel items URLs.
        """
        _ = self.request.translate
        def pack(item):
            url, name, icon=item
            d={
                'URL':self.request.route_url(url),
                'icon':icon,
                'name':name
            }
            return d
        return (pack(item) for item in self.__class__.panel_routes)

    @property
    def body(self):
        return " "

    @property
    def route_url(self):
        return self.request.route_url(self.route_name)

    def answer(self):
        """Do something smart.
        This called from __call__,
        and return value (if not None) set as 'answer'
        global in template rendering.
        """
    def action(self):
        """Make some action, e.g. use POST data.
        """

    def __call__(self):
        self.action()
        answer=self.answer()
        view={'view':self}
        if answer != None:
            view['answer']=answer
        #if self.context != None:
        #    view['context']=self.context
        # template
        # attrs
        self.request.response.headers['Access-Control-Allow-Origin']='*'
        return view

    def active(self, name):
        mname=self.route_name
        if name==mname:
            return "active"
        raise ValueError('wrong route')

    def sparql(self, query, graph):
        """Query a graph, convert all
        answer attributes to python values.
        """
        def tp_(o):
            if o == None:
                return o
            else:
                return o #o.toPython()
        try:
            rset=graph.sparql(query)
        except ParseException as e:
            logger.error("Exception {!r}.".format(e) + "\nSPARQL Query:\n"+self._sparql_err(query, e))
            self.exception=e
            return
        for r in rset:
            yield list(map(tp_, r))

    def _sparql_err(self, query, exc):
        lineno=exc.lineno
        col=exc.col
        s=''
        for i, l in enumerate(query.splitlines()):
            s+=l+"\n"
            if i+1==lineno:
                s+=' '*(col-1)+"^\n"
        return s

    @property
    def include_scripts(self):
        return self.__class__.scripts

@view_config(route_name='archive',renderer='templates/indexLTE.pt',
             request_method="GET", title=_('Document Archive'))
class ArchiveView(View):
    """View for archive
    """
    scripts=View.scripts+[
        ('javascript', 'doc-load-script.js')
    ]

    @property
    def body(self):
        ts=self._("Drag & Drop Files Here")
        return \
"""<div id="dragandrophandler">%s</div>
<br/><br/>
<div id="status1"></div>
<br/><br/>
<div id="doc_table" class="panel panel-default" ></div>
""" % ts

    @property
    def links(self):
        return """
        """

    # @property
    # def scripts(self):
    #     return """
    #     <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
    #     """

    @property
    def tail_script(self):
        """Add a script at the tail of page.
        """

        script = \
'''
var doc_load_setup={{
  uploadUrl:"{uploadUrl}",
  docsUrl:"{docsUrl}",
  htmlReady:function(data){{
    $("#doc_table").html(data);
  }}
}};

'''.format(uploadUrl=self.request.route_url('upload'),
           docsUrl=self.request.route_url('get_docs'))
        return script

    @property
    def style(self):
        return """
#dragandrophandler
{
border:4px dotted #0B85A1;
width:600px;
height:100px;
color:#92AAB0;
text-align:center;vertical-align:middle;
padding:10px 10px 10px 10px;
margin-bottom:10px;
font-size:200%;
}
.progressBar {
    width: 200px;
    height: 22px;
    border: 1px solid #ddd;
    border-radius: 5px;
    overflow: hidden;
    display:inline-block;
    margin:0px 10px 5px 5px;
    vertical-align:top;
}

.progressBar div {
    height: 100%;
    color: #fff;
    text-align: right;
    line-height: 22px; /* same as #progressBar height if we want text middle aligned */
    width: 0;
    background-color: #0ba1b5; border-radius: 3px;
}
.statusbar
{
    border-top:1px solid #A9CCD1;
    min-height:25px;
    width:700px;
    padding:10px 10px 0px 10px;
    vertical-align:top;
}
.statusbar:nth-child(odd){
    background:#EBEFF0;
}
.filename
{
display:inline-block;
vertical-align:top;
width:250px;
}
.filesize
{
display:inline-block;
vertical-align:top;
color:#30693D;
width:100px;
margin-left:10px;
margin-right:5px;
}
.abort{
    background-color:#A8352F;
    -moz-border-radius:4px;
    -webkit-border-radius:4px;
    border-radius:4px;display:inline-block;
    color:#fff;
    font-family:arial;font-size:13px;font-weight:normal;
    padding:4px 15px;
    cursor:pointer;
    vertical-align:top
    }

        """

@view_config(route_name="debug_graph", renderer='templates/indexLTE.pt',
             title=_("Debug graph"))
class GraphView(View):

    __acl__ = [
            (Allow, Authenticated, 'view_debug'),
        ]

    @property
    def body(self):
        FORMAT='n3'
        g=queryUtility(IRDFStorage, name=self.request.GET.get("name","doc"))
        if g == None:
            return "<strong>No such graph found.</strong>"
        s = g.serialize(format=FORMAT).decode("utf-8")
        h = "Graph size: "+str(len(g))+" triples<br/>" + \
            "Graph storage: "+cgi.escape(str(g.store))+" <br/>"
        b = "<pre>"+cgi.escape(s)+"</pre>"
        return h+b

    '''
    def __acl__(self):
        logger.info("-----> ACL query ----")
        return [
            (Allow, Everyone, 'view_debug'),
        ]
    '''

@view_config(route_name="debug_search", renderer='templates/search.pt',
             title=_("Debug search"))
class SearchView(View):

    @property
    def body(self):

        answer=None
        matches=[]
        FORMAT='n3'
        indexer=queryUtility(IIndexer, name="indexer")
        self.doc=queryUtility(IRDFStorage, name="documents")

        query=self.request.GET.get("q", None)

        self.answer=None

        if query == None:
            return "<strong>No Query supplied.</strong>"

        q="Query:" + query + "<br/> resulted to:<br/>"
        if indexer == None:
            return q+"<strong>No SEARCH engine present!</strong>"
        self.answer=indexer.search(query)

        ms=[]

        for m in self.answer['matches']:
            for r in self.proc_match(m):
                ms.append(r)

        self.matches=ms

        return q

    def proc_match(self, match):
        for row in self.proc_attrs(match['attrs']):
            yield row+[match['attrs']['hid'], match['id'], match['weight']/1000.]

    def proc_attrs(self, attrs):
        hid=attrs['hid']
        key=hexdigest(hid)
        #l=Literal(key)
        logger.debug((hid, key))
        Q='''
        SELECT DISTINCT ?date ?title ?file ?id ?mimetype
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:annotatedAt ?date .
           ?ann oa:hasTarget ?target .
           ?ann oa:hasBody ?body .
        OPTIONAL { ?target nie:title ?title } .
           ?body nie:identifier "''' + key + '''" .
           ?target nfo:fileName ?file .
           ?target nmo:mimeType ?mimetype .
           ?target nie:identifier ?id .
        }
        '''

        logger.debug(Q)
        yield from self.sparql(Q, self.doc)

@view_config(route_name="get_docs", renderer='templates/doc_table.pt')
class DocsView(View):
    @property
    def docs(self):
        g=getUtility(IRDFStorage, "documents")
        Q="""
        SELECT DISTINCT ?date ?title ?id ?file ?mimetype
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:annotatedAt ?date .
           ?ann oa:hasTarget ?target .
        OPTIONAL { ?target nie:title ?title } .
           ?target nie:identifier ?id .
           ?target nfo:fileName ?file .
           ?target nmo:mimeType ?mimetype .
        FILTER ( ?date>="$min"^^xsd:dateTime && ?date<="$max"^^xsd:dateTime)
        }
        """
        now=datetime.datetime.utcnow()
        dmin=datetime.timedelta(days=-5)
        dmax=datetime.timedelta(days=+1)
        tmin=now+dmin
        tmax=now+dmax
        Q=Template(Q).substitute(
                   min=tmin.strftime(DATE_TIME_FORMAT),
                   max=tmax.strftime(DATE_TIME_FORMAT))
        qres=g.sparql(Q)
        return qres

class SendDocView(View):
    """Send a document
    """
    Q_doc="""
    SELECT DISTINCT ?file ?mimetype
    WHERE {{
      ?ann a oa:Annotation .
      ?ann oa:hasTarget ?target .
      ?target nie:identifier "{}" .
      ?target nfo:fileName ?file .
    OPTIONAL {{ ?target nmo:mimeType ?mimetype }} .
    }}
    """

    Q_ann="""
    SELECT DISTINCT ?mimetype
    WHERE {{
      ?ann a oa:Annotation .
      ?ann oa:hasBody ?body .
      ?body nie:identifier "{}" .
    OPTIONAL {{ ?body nmo:mimeType ?mimetype }} .
    }}
    """

    def __call__(self):
        req=self.request
        doc_id=req.GET.get('doc_id',None)
        ann_id=req.GET.get('ann_id',None)
        doc=getUtility(IRDFStorage, name='documents')
        if doc_id:
            Q=self.Q_doc.format(doc_id)
            for (fileName, mimeType) in self.sparql(Q, doc):
                return self.serve(doc_id, content_type=mimeType, file_name=fileName, content=True)
        if ann_id:
            for (mimeType,) in self.sparql(self.Q_ann.format(ann_id), doc):
                logger.debug("Serving hasBody of mimeType:"+str(mimeType))
                return self.serve(ann_id, content_type=mimeType, file_name="annotation", content=False)
        req.response.status_code=404
        return Response("<h>Document not found.</h>", content_type='text/html')

    def serve(self, key, content_type=None, file_name=None, content=True):
        storage=getUtility(IContentStorage, name='content')
        body=storage.get(key)

        f = tempfile.NamedTemporaryFile()
        f.write(body)
        f.seek(0,0)
        mimeType=content_type
        if mimeType == None and content:
            mimeType == "application/octet-stream"
        elif mimeType == None and not content:
            if content.upper().find("</BODY"):
                mimeType="text/html"
                file_name+='.html'
            else:
                mimeType='text/plain'
                file_name+=".txt"
        response=FileResponse(f.name, request=self.request, content_type=mimeType)
        # FIXME check file if it has been closed
        if content:
            response.headers['Content-Disposition'] = ("attachment; filename={}".format(file_name))
            response.headers['Content-Description'] = 'File Transfer'
        return response


@view_config(route_name="get_doc")
class ShowDocView(SendDocView):
    """Show a document
    """

    def serve(self, key, content_type=None, file_name=None, content=True):
        storage=getUtility(IContentStorage, name='content')
        try:
            body=storage.get(key)
        except ValueError:
            return Response("<h>Cannot find document with ID={}</h>".format(key))
        mimeType=content_type
        if mimeType == None and content:
            mimeType == "application/octet-stream"
        elif mimeType == None and not content:
            if content.upper().find("</BODY"):
                mimeType="text/html"
                file_name+='.html'
            else:
                mimeType='text/plain'
                file_name+=".txt"
        if not content:
            body=body.replace(br"\n",b"\n").replace(br'\r',b'')
        response = Response(body=body, content_type=mimeType)
        return response

@view_config(route_name="login",renderer="templates/loginLTE.pt",
             title=_("Login"), request_method=("GET", "POST"))
class LoginRegisterView(View):

    @property
    def register(self):
        return self.route_name=='register'

    @property
    def login(self):
        return self.route_name=="login"

    @property
    def prompt(self):
        _=self._
        if self.register:
            return _("Register new user")
        else:
            return _("Enter Your account data")

    @property
    def sys_info(self):
        _=self._
        return _("Cellula")

    def action(self):
        print ("-----> ", list(self.request.POST.items()))
        print (self.request.POST.get("email"))
        print (self.request.POST.get("password"))
        print (self.request.POST.get("password_confirm"))
        return True

@view_config(route_name="register",renderer="templates/loginLTE.pt",
             title=_("Register"))
class RegisterView(LoginRegisterView):
    pass

@view_config(route_name='maintain',renderer='templates/maintain.pt',
             title=_("Maintainance View"))
class MaintainanceView(View):
    def answer(self):
        tasks=GetQueue('tasks')
        tasks.put(MetadataRestoreTask(), block=False)
        tasks.put(ContentIndexTask(), block=False)

@view_config(route_name='metal_test',renderer='templates/test.pt',
             title=_("Test View"))
class MetalTestView(View):
    pass

@view_config(route_name='email',renderer='templates/indexLTE.pt',
             title=_("E-Mail"))
class EmailView(View):
    pass

@view_config(route_name='dashboard',renderer='templates/indexLTE.pt',
             title=_('Dashboard'))
class DashboardView(View):
    pass

@view_config(route_name='upload', request_method="POST", renderer='json')
class UploadDocView(View):
    def __call__(self):
        request=self.request
        _ = request.translate

        body = request.body
        headers = request.headers

        things={}
        things.update(headers)

        fs=request.POST.get('file', None)

        if fs == None:
            request.response.status_code=400
            return { 'error':'no file', 'explanation':'check input form if it contains "file" field' }

        def _(v):
            v=v.strip()
            if v.startswith('"') and v.endswith('"'):
                v=v.strip('"')
                if v.startswith("'") and v.endswith("'"):
                    v=v.strip("'")
                    return v
                    things.update({k:_(v) for k,v in fs.headers.items()})

        if fs.filename == None:
            request.response.status_code=400
            return { 'error':'no file', 'explanation':'check input form if it contains "file" field of type file' }

        #hash128=(request.POST.get("hash128_low", None),request.POST.get("hash128_high", None));
            #hash128=[int(d) for d in hash128];

        #client_hash=hexdigest(hash128);

        things['File-Name']=fs.filename

        storage=getUtility(IContentStorage, name='content')

        content=fs.value #file
        doc_id=things['id']=storage.hash(content)
        rc=storage.resolve(doc_id)
        logger.debug((rc, doc_id, storage.db.error()))
        if rc:
            request.response.status_code=400
            return { 'error':'already exists', 'explanation':'the file is already stored' }

        headers=things
        tasks=GetQueue('tasks')

        tasks.put(DocumentAcceptingTask(content, headers), block=False)
        logger.info("Task Queue has %d tasks undone" % tasks.qsize())

        request.response.status_code=201

        things['result']='file stored'

        things['user-id']="eugeneai@npir.ru"

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(things)

        return things

def includeme(config):
    #config.scan("icc.cellula.views")
    config.scan()
    config.add_route('dashboard', "/")
    config.add_route('archive', "/archive")
    config.add_route('email', "/mail")
    config.add_route('upload', "/file_upload")
    config.add_route('get_docs', "/docs")
    config.add_route('get_doc', "/doc")

    config.add_route('login', "/login")
    config.add_route('register', "/register")

    config.add_route('debug_graph', "/archive_debug")
    config.add_route('debug_search', "/search")
    config.add_route('metal_test', "/metal")
    config.add_route('maintain', "/maintain")

    config.add_subscriber('icc.cellula.subscribers.add_base_template',
                      'pyramid.events.BeforeRender')

    #config.scan()
