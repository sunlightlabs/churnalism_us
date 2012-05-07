alert('it works!');

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






