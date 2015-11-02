""" Cornice services.
"""
from cornice import Service
from pyramid.response import Response
from pyramid.view import view_config
from pprint import pprint
from icc.contentstorage.interfaces import IDocumentStorage
from zope.component import getUtility

from icc.cellula.extractor.interfaces import IExtractor
from icc.cellula.indexer.interfaces import IIndexer
from icc.rdfservice.interfaces import IRDFStorage

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

class ArchiveView(View):
    """View for archive
    """

    @property
    def body(self):
        ts=self._("Drag & Drop Files Here")
        return \
"""<div id="dragandrophandler">%s</div>
<br><br>
<div id="status1"></div>""" % ts

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

            $("#status1").append("File upload Done<br>");
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
        return { 'error':'no file', 'explanation':'check input form it it contains "file" field' }

    things.update(fs.headers)

    """
    if fs.filename != None:
        o=open(fs.filename,"wb")
        o.write(fs.value)
    else:
    """
    if fs.filename == None:
        request.response.status_code=400
        return { 'error':'no file', 'explanation':'check input form it it contains "file" field' }

    things['FileName']=fs.filename

    storage=getUtility(IDocumentStorage, name='content')

    """
    if storage.exists(fs.value): # is it an error?
        request.response.status_code=400
        return { 'error':'content already exists', 'explanation':'a file with the same content has been uploaded already' }
    """

    rc_id=storage.put(fs.value)

    #view=ArchiveView(*args, title=_('Document Archive'))
    #return view()
    request.response.status_code=201
    things['id']=rc_id
    things['result']='file stored'

    # extract here

    extractor=getUtility(IExtractor, name='extractor')

    ext_data=extractor.extract(fs.value, things)

    ext_things={}
    ext_things.update(things)
    ext_things.update(ext_data)

    content_extractor=getUtility(IExtractor, name='content')

    cont_data=content_extractor.extract(fs.value, ext_things)

    if not 'text-body' in cont_data:
        recoll_extractor=getUtility(IExtractor, name='recoll')
        ext_things.update(cont_data)
        cont_data=recoll_extractor.extract(fs.value, ext_things)

    text_p=things['text-body-presence']='text-body' in cont_data

    things.update(cont_data)
    if text_p:
        text_body=cont_data['text-body']
        text_id=storage.put(text_body)
        things['text-id']=text_id
        #indexer=getUtility(IIndexer, "indexer")
        #indexer.put(text_body, things)
        # index text

    # Add user data
    things['user-email']="eugeneai@npir.ru"
    things['user-id']="eugeneai"

    doc_meta = getUtility(IRDFStorage, name='documents')
    doc_meta.store(things)

    if text_p:
        del things['text-body']

    #print(cont_data)
    return things

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
    config.add_route('upload', "/file_upload")
