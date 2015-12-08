var async_renderer = function(setup) {
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
    target_node.html("<h2>Something wrong</h2>");  // FIXME remove on going production.
    setup.template_compiled=dust.compileFn(src_template.html(), setup.template);
    var base = dust.makeBase({
        hello: function() {
            return "Hello!";
        },
        rel:function(relation, options) {
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
        }
    });

    var context=base.push({
        foo:"bar"
    });

    dust.render(setup.template, context,
                function(err, out) {
                    if (err !== null) {
                        console.error(err);
                    };
                    if (out !== null) {
                        target_node.html(out);
                    };
                }
               );

    var data={};

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

    function pEscape(term, divider) {
        if (term.length===0) {
            return "";
        };
        if (term[0]===term[0].toUpperCase()) {
            term="'"+term+"'";
        };
        return term+":";
    };

    function pTerm(term) {
        var ns,t;
        if (rel.indexOf(":")===-1) {
            ns='';
            t=term;
        } else {
            var a=term.split(":");
            ns=a[0];
            t=a[1];
            a=null;
        };
        return pEscape(ns,":")+pEscape(term,'');
    };

    function genQuery(item, relation, graph_name) {
        var query="icc:triple("+pTerm(item.subject)+","+pTerm(relation)+",Object,"+graph_name+")";
        return query;
    };

    // var pengine = new Pengine(pengine_setup);
};
