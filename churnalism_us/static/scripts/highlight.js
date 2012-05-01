var OPEN_TAG = '<span class="churnalism-highlight" churnalism:fragment="FRAG_NUMBER">';
var CLOSE_TAG = '</span>';

RegExp.escape = function(text) {
    return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
};

// More info at: http://phpjs.org
/// https://raw.github.com/kvz/phpjs/master/functions/strings/htmlspecialchars_decode.js
function htmlspecialchars_decode (string, quote_style) {
    // http://kevin.vanzonneveld.net
    // +   original by: Mirek Slugen
    // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +   bugfixed by: Mateusz "loonquawl" Zalega
    // +      input by: ReverseSyntax
    // +      input by: Slawomir Kaniecki
    // +      input by: Scott Cariss
    // +      input by: Francois
    // +   bugfixed by: Onno Marsman
    // +    revised by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
    // +   bugfixed by: Brett Zamir (http://brett-zamir.me)
    // +      input by: Ratheous
    // +      input by: Mailfaker (http://www.weedem.fr/)
    // +      reimplemented by: Brett Zamir (http://brett-zamir.me)
    // +    bugfixed by: Brett Zamir (http://brett-zamir.me)
    // *     example 1: htmlspecialchars_decode("<p>this -&gt; &quot;</p>", 'ENT_NOQUOTES');
    // *     returns 1: '<p>this -> &quot;</p>'
    // *     example 2: htmlspecialchars_decode("&amp;quot;");
    // *     returns 2: '&quot;'
    var optTemp = 0,
        i = 0,
        noquotes = false;
    if (typeof quote_style === 'undefined') {
        quote_style = 2;
    }
    string = string.toString().replace(/&lt;/g, '<').replace(/&gt;/g, '>');
    var OPTS = {
        'ENT_NOQUOTES': 0,
        'ENT_HTML_QUOTE_SINGLE': 1,
        'ENT_HTML_QUOTE_DOUBLE': 2,
        'ENT_COMPAT': 2,
        'ENT_QUOTES': 3,
        'ENT_IGNORE': 4
    };
    if (quote_style === 0) {
        noquotes = true;
    }
    if (typeof quote_style !== 'number') { // Allow for a single string or an array of string flags
        quote_style = [].concat(quote_style);
        for (i = 0; i < quote_style.length; i++) {
            // Resolve string input to bitwise e.g. 'PATHINFO_EXTENSION' becomes 4
            if (OPTS[quote_style[i]] === 0) {
                noquotes = true;
            } else if (OPTS[quote_style[i]]) {
                optTemp = optTemp | OPTS[quote_style[i]];
            }
        }
        quote_style = optTemp;
    }
    if (quote_style & OPTS.ENT_HTML_QUOTE_SINGLE) {
        string = string.replace(/&#0*39;/g, "'"); // PHP doesn't currently escape if more than one 0, but it should
        // string = string.replace(/&apos;|&#x0*27;/g, "'"); // This would also be useful here, but not a part of PHP
    }
    if (!noquotes) {
        string = string.replace(/&quot;/g, '"');
    }
    // Put this in last place to avoid escape being double-decoded
    string = string.replace(/&amp;/g, '&');

    return string;
}

var highlight_match = function (p, match, frag_number) {
    var html = htmlspecialchars_decode(jQuery(p).html());
    var haystack = html.replace(/[\x00-\x2F]/g, ' ').toLowerCase();
    var needle = match.replace(/[\x00-\x2F]/g, '\x00').toLowerCase();
    var needle_pattern = RegExp.escape(needle).replace(/[\x00]+/g, '[\\x00-\\x2F]*?');
    var needle_regex = new RegExp(needle_pattern, 'i');
    var html_match = needle_regex.exec(html);
    if (html_match == null) {
        console.log('No match for: ', needle_regex);
    } else {
        var offset = html.indexOf(html_match[0]);
        if (offset >= 0) {
            var prelude = html.slice(0, offset);
            var matched = html.slice(offset, offset + html_match[0].length);
            var postlude = html.slice(offset + html_match[0].length);
            jQuery(p).html(prelude + OPEN_TAG.replace('FRAG_NUMBER', frag_number) + matched + CLOSE_TAG + postlude);
        } else {
            console.log('No match for already-found needle: ', html_match[0]);
        }
    }
};



