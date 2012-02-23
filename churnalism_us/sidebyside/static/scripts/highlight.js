var PREFIX_LENGTH = 6;
var OPEN_TAG = '<i style="background: yellow none;">';
var CLOSE_TAG = '</i>';

var highlight_match = function (p, match) {
    var html = jQuery(p).html().replace(/&nbsp;/g, ' ');
    var half_length = Math.floor(match.length / 2);
    while (half_length >= PREFIX_LENGTH) {
        var prefix = match.slice(0, half_length).trim();
        var suffix = match.slice(-half_length).trim();
        var prefix_offset = html.indexOf(prefix);
        var prefix_boundary = prefix_offset + prefix.length;
        var after_prefix = html.slice(prefix_boundary);
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
};
