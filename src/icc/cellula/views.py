""" Cornice services.
"""
from cornice import Service
from pyramid.response import Response, FileResponse
from pyramid.view import view_config
from pprint import pprint, pformat
from icc.contentstorage.interfaces import IContentStorage
from icc.contentstorage import hexdigest
from zope.component import getUtility, queryUtility

from icc.rdfservice.interfaces import IRDFStorage, IGraph
from icc.cellula.indexer.interfaces import IIndexer

from rdflib import Literal
from pyparsing import ParseException
import tempfile

import cgi
from icc.cellula.tasks import DocumentAcceptingTask, GetQueue
import logging
logger=logging.getLogger('icc.cellula')

class View(object):
    def __init__(self, *args, **kwargs):
        if args:
            self.request=args[1]
            self.traverse=args[0]
        else:
            self.request=kwargs.get('request', None)
            self.traverse=kwargs.get('traverse', None)
        _ = self.request.translate
        self._=_
        kw=kwargs
        self.title=kw.get('title', _('====TITLE====='))
        self.context=kw.get('context', kw.get('ob',None))
        self.exception=None

    @property
    def body(self):
        return " "

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
        # template
        # attrs
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
        def _(o):
            if o == None:
                return o
            else:
                return o.toPython()
        try:
            rset=graph.query(query)
        except ParseException as e:
            logger.error("Exception {!r}.".format(e) + "\nSPARQL Query:\n"+self._sparql_err(query, e))
            self.exception=e
            return
        for r in rset:
            yield list(map(_, r))

    def _sparql_err(self, query, exc):
        lineno=exc.lineno
        col=exc.col
        s=''
        for i, l in enumerate(query.splitlines()):
            s+=l+"\n"
            if i+1==lineno:
                s+=' '*(col-1)+"^\n"
        return s

class ArchiveView(View):
    """View for archive
    """

    @property
    def body(self):
        ts=self._("Drag & Drop Files Here")
        return \
"""<div id="dragandrophandler">%s</div>
<br/><br/>
<div id="status1"></div>
<br/><br/>
<div id="doc_table"></div>
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
function renew_doc_list() {
    $.get(
        "/docs",
        function (data) {
            $("#doc_table").html(data); //replaceWith(data);
        }
    );
}


function sendFileToServer(formData,status)
{
//    var uploadURL ="http://hayageek.com/examples/jquery/drag-drop-file-upload/upload.php"; //Upload URL
    var uploadURL = "''' + self.request.route_url('upload') + '''"//QQQ
    var extraData ={}; //Extra Data.
    var jqXHR=$.ajax({
            xhr: function() {
            var xhrobj = $.ajaxSettings.xhr();
            if (xhrobj.upload) {
                    xhrobj.upload.addEventListener('progress', function(event) {
                        var percent = 0;
                        var position = event.loaded || event.position;
                        var total = event.total;
                        if (event.lengthComputable) {
                            percent = Math.ceil(position / total * 100);
                        }
                        //Set progress
                        status.setProgress(percent);
                    }, false);
                }
            return xhrobj;
        },
    url: uploadURL,
    type: "POST",
    contentType:false,
    processData: false,
        cache: false,
        data: formData,
        success: function(data){
            status.setProgress(100);

            // $("#status1").append("File upload Done<br>");
            renew_doc_list();
        }
    });

    status.setAbort(jqXHR);
}

var rowCount=0;
function createStatusbar(obj)
{
     rowCount++;
     var row="odd";
     if(rowCount %2 ==0) row ="even";
     this.statusbar = $("<div class='statusbar "+row+"'></div>");
     this.filename = $("<div class='filename'></div>").appendTo(this.statusbar);
     this.size = $("<div class='filesize'></div>").appendTo(this.statusbar);
     this.progressBar = $("<div class='progressBar'><div></div></div>").appendTo(this.statusbar);
     this.abort = $("<div class='abort'>Abort</div>").appendTo(this.statusbar);
     obj.after(this.statusbar);

    this.setFileNameSize = function(name,size)
    {
        var sizeStr="";
        var sizeKB = size/1024;
        if(parseInt(sizeKB) > 1024)
        {
            var sizeMB = sizeKB/1024;
            sizeStr = sizeMB.toFixed(2)+" MB";
        }
        else
        {
            sizeStr = sizeKB.toFixed(2)+" KB";
        }

        this.filename.html(name);
        this.size.html(sizeStr);
    }
    this.setProgress = function(progress)
    {
        var progressBarWidth =progress*this.progressBar.width()/ 100;
        this.progressBar.find('div').animate({ width: progressBarWidth }, 10).html(progress + "% ");
        if(parseInt(progress) >= 100)
        {
            this.abort.hide();
        }
    }
    this.setAbort = function(jqxhr)
    {
        var sb = this.statusbar;
        this.abort.click(function()
        {
            jqxhr.abort();
            sb.hide();
        });
    }
}
function handleFileUpload(files,obj)
{
   for (var i = 0; i < files.length; i++)
   {
        var fd = new FormData();
        fd.append('file', files[i]);

        var status = new createStatusbar(obj); //Using this we can set progress.
        status.setFileNameSize(files[i].name,files[i].size);
        sendFileToServer(fd,status);

   }
}

$(document).ready(function()
{
renew_doc_list();
var obj = $("#dragandrophandler");
obj.on('dragenter', function (e)
{
    e.stopPropagation();
    e.preventDefault();
    $(this).css('border', '2px solid #0B85A1');
});
obj.on('dragover', function (e)
{
     e.stopPropagation();
     e.preventDefault();
});
obj.on('drop', function (e)
{

     $(this).css('border', '2px dotted #0B85A1');
     e.preventDefault();
     var files = e.originalEvent.dataTransfer.files;

     //We need to send dropped files to Server
     handleFileUpload(files,obj);
});
$(document).on('dragenter', function (e)
{
    e.stopPropagation();
    e.preventDefault();
});
$(document).on('dragover', function (e)
{
  e.stopPropagation();
  e.preventDefault();
  obj.css('border', '2px dotted #0B85A1');
});
$(document).on('drop', function (e)
{
    e.stopPropagation();
    e.preventDefault();
});
});
'''
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

class GraphView(View):

    @property
    def body(self):
        FORMAT='n3'
        g=queryUtility(IGraph, name=self.request.GET.get("name","doc"))
        if g == None:
            return "<strong>No such graph found.</strong>"
        s = g.serialize(format=FORMAT).decode("utf-8")
        h = "Graph size: "+str(len(g))+" triples<br/>" + \
            "Graph storage: "+cgi.escape(str(g.store))+" <br/>"
        b = "<pre>"+cgi.escape(s)+"</pre>"
        return h+b

class SearchView(View):

    @property
    def body(self):
        answer=None
        matches=[]
        FORMAT='n3'
        indexer=queryUtility(IIndexer, name="indexer")
        self.doc=queryUtility(IGraph, name="doc")

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
        SELECT DISTINCT ?date ?title ?file ?mimetype
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:annotatedAt ?date .
           ?ann oa:hasTarget ?target .
        OPTIONAL { ?target nie:title ?title } .
           ?target nao:identifier "''' + key + '''" .
           ?target nfo:fileName ?file .
           ?target nmo:mimeType ?mimetype .
        }
        '''
        logger.debug(Q)
        yield from self.sparql(Q, self.doc)

class DocsView(View):
    @property
    def docs(self):
        g=getUtility(IGraph, "doc")
        Q="""
        SELECT DISTINCT ?date ?title ?id ?file ?mimetype
        WHERE {
           ?ann a oa:Annotation .
           ?ann oa:annotatedAt ?date .
           ?ann oa:hasTarget ?target .
        OPTIONAL { ?target nie:title ?title } .
           ?target nao:identifier ?id .
           ?target nfo:fileName ?file .
           ?target nmo:mimeType ?mimetype .
        }
        """
        qres=g.query(Q)
        return qres

class SendDocView(View):
    """Send a document
    """
    Q_doc="""
    SELECT DISTINCT ?file ?mimetype
    WHERE {{
      ?ann a oa:Annotation .
      ?ann oa:hasTarget ?target .
      ?target nao:identifier "{}" .
      ?target nfo:fileName ?file .
    OPTIONAL {{ ?target nmo:mimeType ?mimetype }} .
    }}
    """

    Q_ann="""
    SELECT DISTINCT ?mimetype
    WHERE {{
      ?ann a oa:Annotation .
      ?ann oa:hasBody ?body .
      ?body nao:identifier "{}" .
    OPTIONAL {{ ?body nmo:mimeType ?mimetype }} .
    }}
    """

    def __call__(self):
        req=self.request
        doc_id=req.GET.get('doc_id',None)
        ann_id=req.GET.get('ann_id',None)
        doc=getUtility(IGraph, name='doc')
        if doc_id:
            Q=self.Q_doc.format(doc_id)
            for fileName, mimeType in self.sparql(Q, doc):
                return self.serve(doc_id, content_type=mimeType, file_name=fileName, content=True)
        if ann_id:
            for mimeType in self.sparql(self.Q_ann.format(ann_id), doc):
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

# ---------------- Actual routes ------------------------------------------

@view_config(route_name='dashboard',renderer='templates/index.pt')
def get_dashboard(*args):
    request=args[1]
    _ = request.translate
    view=View(*args, title=_('Dashboard'))
    return view()

@view_config(route_name='archive',renderer='templates/index.pt', request_method="GET")
def get_archive(*args):
    request=args[1]
    _ = request.translate
    view=ArchiveView(*args, title=_('Document Archive'))
    return view()

@view_config(route_name='upload', request_method="POST", renderer='json')
def post_archive(*args):
    request=args[1]
    _ = request.translate

    body = request.body
    headers = request.headers

    things={}
    things.update(headers)

    fs=request.POST.get('file', None)

    if fs == None:
        request.response.status_code=400
        return { 'error':'no file', 'explanation':'check input form if it contains "file" field' }

    things.update(fs.headers)

    if fs.filename == None:
        request.response.status_code=400
        return { 'error':'no file', 'explanation':'check input form if it contains "file" field of type file' }

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

@view_config(route_name="get_docs", renderer='templates/doc_table.pt')
def docs(*args, **kwargs):
    request=args[1]
    _ = request.translate
    view=DocsView(*args)
    return view()

@view_config(route_name="get_doc")
def get_doc(*args, **kwargs):
    request=args[1]
    _ = request.translate
    view=SendDocView(*args)
    return view()

@view_config(route_name="debug_graph", renderer='templates/index.pt')
def get_debug(*args):
    request=args[1]
    _ = request.translate
    name=request.GET.get("name", "doc")
    view=GraphView(*args, title=_("Debug graph '%s'") % name)
    return view()

@view_config(route_name="debug_search", renderer='templates/search.pt')
def get_search(*args):
    request=args[1]
    _ = request.translate
    view=SearchView(*args, title=_("Debug search"))
    return view()

@view_config(route_name='email',renderer='templates/index.pt')
def get_email(*args):
    request=args[1]
    _ = request.translate
    view=View(*args, title=_("E-Mail"))
    return view()

@view_config(route_name='metal_test',renderer='templates/test.pt')
def get_metal(*args):
    request=args[1]
    _ = request.translate
    view=View(*args, "Test View")
    return view()

def includeme(config):
    #config.scan("icc.cellula.views")
    config.scan()
    config.add_route('dashboard', "/")
    config.add_route('archive', "/archive")
    config.add_route('email', "/mail")
    config.add_route('upload', "/file_upload")
    config.add_route('get_docs', "/docs")
    config.add_route('get_doc', "/doc")

    config.add_route('debug_graph', "/archive_debug")
    config.add_route('debug_search', "/search")
    config.add_route('metal_test', "/metal")


    config.add_subscriber('icc.cellula.subscribers.add_base_template',
                      'pyramid.events.BeforeRender')

    #config.scan()
