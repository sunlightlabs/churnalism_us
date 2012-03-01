var PREFIX_LENGTH = 6;
var OPEN_TAG = '<i style="background: yellow none;">';
var CLOSE_TAG = '</i>';

var highlight_match = function (p, match, case_insensitive) {
    var html = jQuery(p).html().replace(/&nbsp;/g, ' ');
    var search_html = (case_insensitive) ? html.toLowerCase() : html;
    var search_match = (case_insensitive) ? match.toLowerCase() : match;
    var half_length = Math.floor(search_match.length / 2);
    while (half_length >= PREFIX_LENGTH) {
        var prefix = search_match.slice(0, half_length).trim();
        var suffix = search_match.slice(-half_length).trim();
        var prefix_offset = search_html.indexOf(prefix);
        var prefix_boundary = prefix_offset + prefix.length;
        var after_prefix = search_html.slice(prefix_boundary);
        var suffix_offset = after_prefix.indexOf(suffix) + prefix_boundary;
        var suffix_boundary = suffix_offset + suffix.length;
        if ((prefix_offset >= 0) && (suffix_offset >= 0) && (suffix_offset >= prefix_boundary)) {
            var prelude = html.slice(0, prefix_offset);
            var matched = html.slice(prefix_offset, suffix_boundary);
            var postlude = html.slice(suffix_boundary);
            $(p).html(prelude +
                OPEN_TAG +
                matched +
                CLOSE_TAG +
                postlude);
            return;
        } else {
            half_length = Math.ceil(half_length / 2);
        }
    }

    if (! case_insensitive) {
        highlight_match(p, match, true);
    }
};
