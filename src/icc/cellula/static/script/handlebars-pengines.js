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
    if (setup.vars===undefined) {
        //console.error("Var mapping did not supported.");
        //return;
        //setup.vars={subj:}
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
    target_node.html("<h2>Here</h2>");

    var pengine = new Pengine({
        ask: setup.query, // "icc:triple(Subject,rdf:type,oa:'Annotation',document)",
        //        template:'[Subject]',
        chunk:setup.limit,
        server:setup.server,
        onsuccess: handleSuccess,
        onfailure: handleFailure,
        onerror: handleError
    });
    function handleSuccess() {
        data.source=this.data;
        var ans=new Array(this.data.length);
        this.data.forEach(function(answer, i, arr) {
            var val,key;
            var o={};
            for (key in setup.vars) {
                val=setup.vars[key];
                val=answer[val]; // Get the value from query answer as a variable
                o[key]=val;
            };
            ans[i]=o;
        });
        data.answer=ans;
        var html_result=setup.template_compiled(data.answer);
        target_node.html(html_result);
        pengine.stop(); // FIXME Loosing other results.
    };
    function handleFailure() {
        console.info(this.data);
    };
    function handleError() {
        console.error(this.data);
    };
};

Handlebars.registerHelper('subj', function(items, options) {
    var out='';
    var objs=options.data.root;
    for(var i=0, l=objs.length; i<l; i++) {
      out = out + options.fn(objs[i][options.name]);
    };
    return out;
});

Handlebars.registerHelper('erel', function(items, options) {
    var out='';
    /*
     for(var i=0, l=items.length; i<l; i++) {
     out = out + options.fn(items[i].subj);
     };
     return out;
     */
    return options.fn(items);
});

Handlebars.registerHelper('rel', function(item, options) {
  return item;
});
