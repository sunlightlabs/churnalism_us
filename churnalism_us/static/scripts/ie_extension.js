var defaultOptions = {
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
    search_server: 'http://churnalism.sunlightfoundation.com:8080',
    submit_urls: false
};

function load_script(url){
    var head = document.getElementsByTagName('head')[0];
    var scr = document.createElement('script');
    scr.setAttribute('type', 'text/javascript');
    scr.setAttribute('src', url);
    head.appendChild(scr);
}

load_script('/static/scripts/jquery-1.7.1.min.js');
load_script('/static/scripts/extractor.js');

var standardize_quotes = function (text, leftsnglquot, rightsnglquot, leftdblquot, rightdblquot) {
    return text.replace(/[\u2018\u201B]/g, leftsnglquot)
               .replace(/[\u0027\u2019\u201A']/g, rightsnglquot)
               .replace(/[\u201C\u201F]/g, leftdblquot)
               .replace(/[\u0022\u201D"]/g, rightdblquot);
};


jQuery(document).ready(function(){
    jQuery('iframe').each(function(idx, iframe){
        var src = jQuery(iframe).attr('src');
        if (/wmode=opaque/i.test(src)) {
            src = src.replace(/wmode=opaque/i, 'wmode=transparent');
        } else if (src != null) {
            src = src + ((src.indexOf('?') == -1) ? '?' : '&') + 'wmode=transparent';
        } 
        jQuery(iframe).attr('src', src);
    });

    ArticleExtractor(window);
    var article_document = new ExtractedDocument(document);
    var article = article_document.get_article_text();
    article = standardize_quotes(article, "'", "'", '"', '"');
    var title = article_document.get_title();
    var req = {
        'method': 'articleExtracted',
        'url': window.location.href,
        'text': article,
        'title': title
    };
//    chrome.extension.sendRequest(req);
   alert(article)  
});

