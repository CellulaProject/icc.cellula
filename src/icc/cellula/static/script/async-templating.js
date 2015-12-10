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
  console.log(src_template.html());
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
  try {
    setup.template_compiled=dust.compileFn(src_template.html(), setup.template);
  } catch (e){
    console.log(dust.compile(src_template.html(), setup.template));
    console.error(e);
    var lines=src_template.html().split("\n");
    var out='';
    var sp;
    var locs=e.location.start;
    var loce=e.location.end;
    lines.forEach(function(line, i, _) {
      if (i<9) {
        sp=' ';
      } else {
        sp='';
      };
      var ln=i+1;
      out = out + sp + ln +" "+line+'\n';
      if (locs.line===ln) {
        out = out + sp+ ln + " " + new Array(locs.column).join(' ')+"^\n";
      };
    });
    console.log(out);
    lines=null;
    out=null;
    console.log(e.name+" "+locs.line+":("+locs.column+"):"+e.message);
    console.error(e.name+" "+locs.line+":("+locs.column+"):"+e.message);
    debugger;
  };

  var base = dust.makeBase({
    subj: function(chunk, context, bodies) {
      var subject=context.get('subject');
      return chunk.write(subject);
    },
    hello:function(chunk, context, bodies, params) {
      return "Hello!";
    },
    rdf:function(chunk, context, bodies, params) {
      /*
       var psetup={
       __proto__:pengine_main_setup,
       usedata:function (data) {}
       };
       */
      var obj=context.current();
      var ps;
      var new_ob={};
      if (params!==null) {
        ps=params.params;
      } else {
        ps={};
      };
      var rels=new Array();
      var no_props=true;
      for (p in ps) {
        v=ps[p];
        if (p.indexOf(":")>1) {
          if (v===true) {
            rels.push(p);
          } else {
            console.error("Unsupported property mapping: '"+p+"':'"+v+"'");
          };
        } else { // This is not a RDF entity.
          if (v===true) {
            obj=obj[p];
            no_props=false;
          } else {
            var val=v;
            if (typeof v==="string") {
              val=obj[p];
            };
            obj[v]=val;
            no_props=false;  // It seems that the object will be manipulated as a hash.
          };
        };
      };
      if (no_props) {
        if ('subject' in obj) {
          obj=obj.subject;
        };
      };
      var _mfun=function(s) {
          return pTerm(s);
      };
      if (rels.length>0) {
        rels=rels.map(_mfun);
        if (Array.isArray(obj)) {
          obj=obj.map(_mfun);
        } else {
          obj=_mfun(obj);
        };
      };
      if (bodies===null || bodies.block==undefined) {
        return chunk.write(obj);
      };
      var ctx;
      for(var i=0, l=obj.length; i<l; i++) {
        // chunk.render(bodies.block, base.push(subj[i]));
        ctx=context.push(obj[i], i, l);
        chunk.render(bodies.block, ctx);
      };
      return '';
    }
  });


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
      var context=base.push({
        subject:"bar"
      });
      var html_result=setup.template_compiled(data);
      var ctx=base.push(data);
      dust.render(setup.template, ctx, function(err, out) {
        if (err !== null) {
          console.error(err);
          target_node.html("<strong>Template '"+setup.template+"' rendering failed. See error on console </strong>"); // FIXME suggest some more interesting
        };
        if (out !== null) {
          target_node.html(out);
        };
      });
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
    data.subject=ans;
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
    return term+divider;
  };

  function pTerm(term) {
    var ns,t;
    if (term.indexOf(":")===-1) {
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

  var pengine = new Pengine(pengine_setup);
};
