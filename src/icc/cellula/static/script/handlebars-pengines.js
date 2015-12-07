var hb_pengines = (function(){
    var source=$("#entry-template").html();
    var o = {
        template:Handlebars.compile(source)
    };
    return o;
})();

var hb_renderer = function(setup) {
    if (setup.template===undefined) {
        console.error("Template id did not supported.");
        return;
    };
    if (setup.target===undefined) {
        console.error("Target id did not supported.");
        return;
    };
    if (setup.query===undefined) {
        console.error("Prolog query did not supported.");
        return;
    };
    if (setup.subject===undefined) {
        console.error("Subject mapping did not supplied.");
        return;
    };
    if (setup.limit===undefined) {
        setup.limit=100;
    };
    if (setup.server===undefined) {
        setup.server='http://127.0.0.1:3020/pengine';
    };
    var src_template=$(setup.template);
    if (src_template.length==0) {
        console.error("Source template not found.");
        return;
    };
    var target_node=$(setup.target);
    if (target_node.length==0) {
        console.error("Targer Node not found.");
        return;
    };
    setup.template_compiled=Handlebars.compile(src_template.html());
    var data={
    };
    target_node.html("<h2>Something wrong</h2>");

    var pengine_main_setup={
        ask: setup.query, // "icc:triple(Subject,rdf:type,oa:'Annotation',document)",
        //        template:'[Subject]',
        chunk:setup.limit,
        server:setup.server,
        onsuccess: handleSuccess,
        onfailure: handleFailure,
        onerror: handleError,
        usedata: function(data){console.error('Forgot to use data.');}
    };

    var pengine_setup = {
        __proto__: pengine_main_setup,
        usedata: function(data) {
            var html_result=setup.template_compiled(data.answer);
            target_node.html(html_result);
        }
    };

    function handleSuccess() {
        data.source=this.data;
        var ans=new Array(this.data.length);
        this.data.forEach(function(answer, i, arr) {
            var val,key;
            var o={subject:answer[setup.subject]};
            ans[i]=o;
        });
        pengine.stop(); // FIXME Loosing other results.
        data.answer=ans;
        pengine_setup.usedata(data);
    };
    function handleFailure() {
        console.info(this.data);
    };
    function handleError() {
        console.error(this.data);
    };

    function genQuery(item, relation) {
        var query="icc:triple('"+item.subject+"',"+relation+",Object,document)";
    };

    Handlebars.registerHelper('rel', function(relation, options) {

        var psetup={
            __proto__:pengine_main_setup,
            usedata:function (data) {}
        };

        if (options.fn==undefined) {
            return this.subject;
        };
        var out='';
        var ob={subject:''};
        for(var i=0, l=this.length; i<l; i++) {
            ob.subject=this[i].subject;
            out = out + options.fn(ob);
        };
        return out;
    });

    var pengine = new Pengine(pengine_setup);
};