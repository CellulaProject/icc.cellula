var hb_pengines = (function(){
    var source=$("#entry-template").html();
    var o = {
        template:Handlebars.compile(source)
    };
    return o;
})();
