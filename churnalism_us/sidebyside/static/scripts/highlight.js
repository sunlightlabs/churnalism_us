var OPEN_TAG = '<i style="background: yellow none;">';
var CLOSE_TAG = '</i>';

var highlight_match = function (p, match) {
    var html = jQuery(p).html();
    var haystack = html.replace(/[\x00-\x2F]/g, ' ').toLowerCase();
    var needle = match.replace(/[\x00-\x2F]/g, ' ').toLowerCase();
    var offset = haystack.indexOf(needle);
    if (offset >= 0) {
        var prelude = html.slice(0, offset);
        var matched = html.slice(offset, offset + needle.length);
        var postlude = html.slice(offset + needle.length);
        $(p).html(prelude +
            OPEN_TAG +
            matched +
            CLOSE_TAG +
            postlude);
    } else {
        console.log('No match for:', needle);
    }
};

