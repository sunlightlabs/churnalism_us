var OPEN_TAG = '<p class="churnalism-highlight fragment-FRAG_NUMBER">';
var CLOSE_TAG = '</p>';

RegExp.escape = function(text) {
    return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
};

var highlight_match = function (p, match, frag_number) {
    var html = jQuery(p).html().replace(/&nbsp;/g, ' ');
    var haystack = html.replace(/[\x00-\x2F]/g, ' ').toLowerCase();
    var needle = match.replace(/[\x00-\x2F]/g, '\x00').toLowerCase();
    var needle_pattern = RegExp.escape(needle).replace(/[\x00]+/g, '[\\x00-\\x2F]*?');
    var needle_regex = new RegExp(needle_pattern, 'i');
    var html_match = needle_regex.exec(html);
    if (html_match == null) {
        console.log('No match for: ', needle);
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
