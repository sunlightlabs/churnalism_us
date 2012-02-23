var PREFIX_LENGTH = 3;
var SUFFIX_LENGTH = 3;
var OPEN_TAG = '<i style="background: yellow none;">';
var CLOSE_TAG = '</i>';

var eat_chars = function (text, expected) {
    var chars_eaten = 0;
    var found = "";

    var textstream = new String(text);
    var expected_c = expected.substr(0, 1);
    while ((found != expected) && (textstream.length > 0)) {
        var c = textstream.substr(0, 1);
        var textstream = textstream.slice(1);

        if (c == expected_c) {
            found += c;
            expected_c = expected.substr(found.length, 1);
        } else {
            chars_eaten += 1;
        }
    }

    if (found == expected) {
        return [true, chars_eaten];
    } else {
        return [false, found];
    }
};

var highlight_match = function (p, match) {
    /* This function finds the `match` text in the html of the the
    * `p` element. The boundaries of the text are determined, then
    * the html corresponding to the text is wrapped in `OPEN_TAG`
    * and `CLOSE_TAG`
    */

    var text_offset = $(p).text().indexOf(match);
    if (text_offset == -1) {
        /* Throw an exception to force callers to limit their calls to 
        * when they know the `match` text is in the `p` paragraph.
        */
        return;
        throw "highlight_match: given match text not found in given paragraph"
    }

    var match_length = match.length;
    var matches = [];
    while ((matches.length == 0) && (match_length >= PREFIX_LENGTH)) {
        var html = $(p).html();
        var prefix = match.substr(0, match_length);
        var html_offset = html.indexOf(prefix);
        if (html_offset >= 0) {
            var meal = eat_chars(html.slice(html_offset), match);
            if (meal[0]) {
                var prelude = html.slice(0, html_offset);
                var suffix_boundary = html_offset + match.length + meal[1];
                var matched = html.slice(html_offset, suffix_boundary);
                var postlude = html.slice(suffix_boundary);
                $(p).html(prelude +
                    OPEN_TAG +
                    matched +
                    CLOSE_TAG +
                postlude);
            return;
            }
        }

        if (match_length <= (PREFIX_LENGTH * 2)) {
            match_length -= 2;
        } else {
            match_length = Math.ceil(match_length / 2);
        }
    }
};

