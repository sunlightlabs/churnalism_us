
//TO DO
//Figure out how to do options dialogue
//If not, make default options pull from server
//make these fetch from the server 
var Params = {
    'MINIMUM_COVERAGE_PCT': 1,
    'MINIMUM_COVERAGE_CHARS': 300,
    'WARNING_RIBBON_SRC': '/sidebyside/chrome/ribbon/'

};

var sufficient_coverage = function (row) {
    return ((row['coverage'][0] >= Params['MINIMUM_COVERAGE_CHARS']) 
            && (Math.round(row['coverage'][1]) >= Params['MINIMUM_COVERAGE_PCT']));
};

var prevent_scroll = function (event) {
    event.preventDefault();
    event.stopPropagation();
    return false;
};


var inject_comparison_iframe = function (url, loading_url) {
    var overlay = jQuery("#churnalism-overlay");
    if (overlay.length == 0) {
        var mask = $('<div id="churnalism-mask">\r\n</div>');
        var overlay_frame = jQuery('<iframe id="churnalism-iframe" frameborder="0" border="none" ></iframe>');
        overlay = jQuery('<div id="churnalism-overlay"></div>');

        overlay_frame.attr('src', loading_url);
        mask.prependTo("body");
        overlay_frame.appendTo(overlay);
        overlay.prependTo('body');

        var close_overlay = function (click) {
            jQuery("#churnalism-mask").fadeOut(function(){ $("#churnalism-mask").remove(); });
            jQuery("#churnalism-overlay").fadeOut(function(){ $("#churnalism-overlay").remove(); });
        };

        jQuery("#churnalism-close").click(close_overlay);
        jQuery("#churnalism-mask").click(close_overlay);

        jQuery("#churnalism-mask").scroll(prevent_scroll);
        jQuery("#churnalism-mask").bind('mousewheel', prevent_scroll);
        jQuery("#churnalism-overlay").scroll(prevent_scroll);
        jQuery("#churnalism-overlay").bind('mousewheel', prevent_scroll);

        var docwidth = jQuery(document).width();
        var halfdelta = (docwidth - 1000) / 2;
        jQuery("#churnalism-overlay").css('width', '1000px');
        jQuery("#churnalism-overlay").css('left', halfdelta + 'px');

        overlay.fadeIn();
        mask.fadeIn();

        setTimeout(function(){
            overlay_frame.attr('src', url);
        }, 250);
    } else {
        jQuery("#churnalism-iframe").remove();
        var overlay_frame = jQuery('<iframe id="churnalism-iframe"></iframe>');
        overlay_frame.appendTo(overlay);
        overlay_frame.attr('src', url);
    }
};


var comparisonUrl = function (uuid, doctype, docid) {
//    var options = restoreOptions();
    var url = options.search_server + '/sidebyside/chrome/__UUID__/__DOCTYPE__/__DOCID__/';
    url = url.replace('__UUID__', uuid)
             .replace('__DOCTYPE__', doctype)
             .replace('__DOCID__', docid);
    return url;
};



var select_search_result = function (search_results, predicate) {
    var rows = search_results['documents']['rows'];
    return rows.reduce(function(state, row){
        var attr = predicate(row);
        if (attr > state[0]) {
            return [attr, row];
        } else {
            return state;
        }
    }, [null, null])[1];
};


var with_best_search_result = function (text, results, next) {
    var row_coverage_and_density = function(row){ return row['coverage'][0] + row['density']; };
    var best = select_search_result(results, row_coverage_and_density);
    next(best);
};


/*var defaultOptions = {
    sites: [
        "www.reuters.com",
        "hosted.ap.org",
        ".nytimes.com",
        "www.washingtonpost.com",
        "www.ft.com",
        "www.bbc.co.uk/news/...",
        "www.guardian.co.uk",
        "www.dailymail.co.uk",
        "www.telegraph.co.uk",
        "www.prnewswire.com",
        "www.pcmag.com",
        "online.wsj.com",
        "www.usatoday.com",
        "www.latimes.com",
        "www.mercurynews.com",
        "www.nypost.com",
        "www.nydailynews.com",
        "www.denverpost.com",
        "www.freep.com",
        "www.jsonline.com",
        "www.chicagotribune.com",
        ".cnn.com",
        ".time.com",
        "www.miamiherald.com",
        "www.startribune.com",
        "www.newsday.com",
        "www.azcentral.com",
        "www.chron.com",
        "www.suntimes.com",
        "www.dallasnews.com",
        "www.mcclatchydc.com",
        "www.scientificamerican.com",
        "www.sciencemag.org",
        "www.newscientist.com",
    ],
    use_generic_news_pattern: false,
    search_server: 'http://churnalism.sunlightfoundation.com',
    assets_server: 'http://churnalism.sunlightfoundation.com',
    ribbon: '/sidebyside/chrome/ribbon/',
    submit_urls: false,
};
*/
var options;// = defaultOptions;

var valid_domain = function(url, options){

//    check  url against 'article' or 'news'
    if (options['use_generic_news_pattern'] == true){
        if( url.indexOf('news') != -1 || url.indexOf('article') != -1) {
            return true;
        }
    }
//   check url against whitelist
    for( s in options['sites']) {
        if (url.indexOf(options['sites'][s]) != -1){
            return true;
        }
    }  
    return false;
}

var load_results = function(result, request_text){
    result = jQuery.parseJSON(result);
    if (result == null || typeof(result) == 'undefined'){
        console.log("error");
    }
    else {
        with_best_search_result(request_text, result, function(best_match){

            if (best_match && sufficient_coverage(best_match)) {

                //insert iframe notifier
                var ribbon_frame = jQuery('<div id="churnalism-ribbon-container" style="width: 100%; background-color: #FCF8F5;"><iframe src="'+ options['search_server'] + options['ribbon'] + '?domain=' + window.location.href + '" id="churnalism-ribbon" name="churnalism-ribbon" frameborder="0" border="none" height=32 scrolling="no"></iframe></div>');
    //            ribbon_frame.attr('src', options['search_server'] + options['ribbon'] + '?domain=' + window.location.href);
                ribbon_frame.prependTo('body');
                //bind handler events to buttons

                window.addEventListener('message', function(event){
                    if (event.data == 'dismiss_churnalism_ribbon') {
                        $("#churnalism-ribbon-container").slideUp('fast', function(){ $(this).remove(); });
                    } else if (event.data == 'show_churnalism_comparison') {
                        inject_comparison_iframe(comparisonUrl(result.uuid, best_match.doctype, best_match.docid), options['search_server'] + '/sidebyside/ie_loading/');
                        $("#churnalism-ribbon-container").slideUp('fast', function(){ $(this).remove(); });
                    }
                }, false);
            } else {
                console.log('match percentge too low');
                console.log(JSON.stringify(best_match));
            }
        });
    } 
};

function search(article_text, article_title, url) {
    var uuid = UUID.uuid5(UUID.NAMESPACE_URL, url);
    var search_url = options['search_server'] + '/api/search/' + uuid.toString() + '/';
    var xdr = new XDomainRequest();
    xdr.open("GET", search_url );
    xdr.onload = function(){ load_results(xdr.responseText, article_text); };
    xdr.onprogress = function(){};
    xdr.ontimeout = function(){};
    xdr.onerror = function(){ 
        console.log('error or no uuid match');
        var x = new XDomainRequest();
        x.open("POST", options['search_server'] + '/api/search/' );
        x.onload = function(){ load_results(x.responseText, article_text); };
        x.onprogress = function(){};
        x.ontimeout = function(){};
        x.onerror = function(){ 
            console.log('error');
        }
        x.send('url=' + encodeURIComponent(url) + '&text='+ encodeURIComponent(article_text) + '&title=' + encodeURIComponent(article_title));
    }
    xdr.send('url=' + encodeURIComponent(url) + '&text='+ encodeURIComponent(article_text) + '&title=' + encodeURIComponent(article_title));
}






function load_script(url, callback){
 
    var script = document.createElement("script")
    script.type = "text/javascript";
 
    if (script.readyState){  //IE
        script.onreadystatechange = function(){
            if (script.readyState == "loaded" ||
                    script.readyState == "complete"){
                script.onreadystatechange = null;
                callback();
            }
        };
    } else {  //Others
        script.onload = function(){
            callback();
        };
    }
 
    script.src = url;
    document.getElementsByTagName("head")[0].appendChild(script);
    return false;
}

var insert_css = function(url) {
    css = document.createElement('link');
    css.rel = "stylesheet";
    css.type = "text/css";
    css.href = url;
    document.getElementsByTagName("head")[0].appendChild(css);
}

var standardize_quotes = function (text, leftsnglquot, rightsnglquot, leftdblquot, rightdblquot) {
    return text.replace(/[\u2018\u201B]/g, leftsnglquot)
               .replace(/[\u0027\u2019\u201A']/g, rightsnglquot)
               .replace(/[\u201C\u201F]/g, leftdblquot)
               .replace(/[\u0022\u201D"]/g, rightdblquot);
};


//jQuery(document).ready(function(){
var extract_article = function() {
    jQuery('iframe').each(function(idx, iframe){
        var src = jQuery(iframe).attr('src');
        if (jQuery(iframe).attr('id') != 'churnalism_options'){
        
            if(/wmode=opaque/i.test(src)) {
                src = src.replace(/wmode=opaque/i, 'wmode=transparent');
            } else if (src != null) {
                src = src + ((src.indexOf('?') == -1) ? '?' : '&') + 'wmode=transparent';
            } 
        
            jQuery(iframe).attr('src', src);
        }
    });

    
    ArticleExtractor(window);
    var article_document = new ExtractedDocument(document);
    var article = article_document.get_article_text();
    article = standardize_quotes(article, "'", "'", '"', '"');
    var title = article_document.get_title();
    var req = {
        'url': window.location.href,
        'text': article,
        'title': title
    };
    result = search(article, title, req['url']);
};

var receive_message = function(e) {
    if(e.data.substr(0, 22) == 'var churnalism_options'  && e.origin !=="http://churnalism.sunlightfoundation.org"){
        eval(e.data);
        options = churnalism_options;
        console.log('options set');
        
        jQuery("#churnalism_options").hide();
        jQuery("#churnalism-mask").hide();

        if (valid_domain(window.location.href, options)){
            kickoff(); //start the chain of events
        }
        else {
            
            //    check url against local news affiliates, need to get list from server
            var xdr = new XDomainRequest();
            var match = false;
            xdr.open("GET", options['search_server'] + '/static/localnews.json' );
            xdr.onload = function(){ 
                local_sites = JSON.parse(xdr.responseText);
                for (ls in local_sites){
                   if(window.location.href.indexOf(ls) != -1){
                        kickoff();
                        return;
                   }  
                }
            };
            xdr.onprogress = function(){};
            xdr.ontimeout = function(){};
            xdr.onerror = function(){ 
                console.log('error');
            }
            xdr.send();

        }
    } else if (e.data == 'enlarge_iframe'){

        var docwidth = jQuery(document).width();
        var halfdelta = (docwidth - 850) / 2;

        jQuery('body').append('<div id="churnalism-mask" style="display:block;position:fixed; top:0; left:0; margin:0; padding:0;height:100%; width:100%; background-color: gray;; opacity:.9; z-index: 2137483639;"></div>');
        jQuery('#churnalism-mask').css('height', jQuery(document).height());
        jQuery("#churnalism_options").css('z-index', '2137483640').css('top', '100px').css('left', halfdelta + 'px').css('position', 'absolute');
        jQuery("#churnalism_options")[0].width=900;
        jQuery("#churnalism_options")[0].height=1150;
    } else {
        console.log("domains don't match");
    }
}



window.addEventListener("message", receive_message, false);

//add iframe for churnalism dummy page, use for LocalStorage 
jQuery('body').append('<iframe id="churnalism_options" src="http://churnalism.sunlightfoundation.com/iframe/" height="0" width="0" frameborder="0"></iframe>');

var kickoff = function() {
    //insert_css(options['assets_server'] + '/static/styles/ie_extension.css');
    insert_css('http://churnalism.sunlightfoundation.com/static/styles/ie_extension.css');
    //make sure options iframe loads
 //  window.setTimeout( function() { 

    load_script(options['search_server'] + '/static/scripts/core-min.js', function(){
        load_script(options['search_server'] + '/static/scripts/sha1-min.js', function(){
            load_script(options['search_server'] + '/static/scripts/uuid35.js', function(){
                load_script(options['search_server'] + '/static/scripts/jquery-1.7.1.min.js', function(){
                    load_script(options['search_server'] + '/static/scripts/extractor.js', extract_article );
                });
            });
        });
    });

 
//                                }, 5000); //have to make sure options load before conducting search
}
