(function(){
    RegExp.prototype.findAll = function (haystack) {
        var matches = [];
        while (true) {
            var m = this.exec(haystack);
            if (m == null) {
                return matches;
            }

            var firstIndex = this.lastIndex - m[0].length;
            matches.push({
                    begin: firstIndex,
                    end: this.lastIndex,
                    text: m[0]
                });
        }
    };

    var mark_blank_lines = function (text, bitmap) {
        var blank_line_pattern = /(\r|\n|\r\n|\n\r)+\s+(\r|\n|\r\n|\n\r)+/gm;
        var blank_lines = blank_line_pattern.findAll(text);
        for (var ix = 0; ix < blank_lines.length; ix++) {
            var begin = blank_lines[ix].begin;
            var end = blank_lines[ix].end;
            var text = blank_lines[ix].text;
            for (var x = begin; x < end; x++) {
                bitmap[x] = -2;
            }
        }
    };

    var mark_paragraph_breaks = function (text, bitmap) {
        var singular_break_pattern = /(\r\n|\n\r|\r|\n)/g;
        var consequtive_break_pattern = /(\r\n|\n\r|\r|\n){2,}/g;
        var break_pattern = consequtive_break_pattern.test(text) ? consequtive_break_pattern : singular_break_pattern;
        var breaks = break_pattern.findAll(text);

        jQuery(breaks).each(function(bx, brk){
            for (var ix = brk.begin; ix < brk.end; ix++) {
                bitmap[ix] = -2;
            }
        });
    };

    var fragment_open_tag = function (n) {
        return '<span class="churnalism-highlight" churnalism:fragment="' + n + '">';
    };

    var fragment_close_tag = function () {
        return '</span>';
    };

    var fragment_firstchar = function (ch) {
        return ['<span class="churnalism-highlight-firstchar">',
                ch,
                '</span>'
                ].join('');
    };

    var fragment_lastchar = function (ch) {
        return ['<span class="churnalism-highlight-lastchar">',
                (ch.charCodeAt(0) == 10) ? '&nbsp;' : ch,
                '</span>'
                ].join('');
    };

    var rewrite_text = function (text, bitmap) {
        var chain = [];
        var link = '';
        var c = null;
        var d = null;
        for (var ix = 0; ix < bitmap.length; ix++) {
            c = bitmap[ix];

            if (d == c) {
                if (d == -2) {
                    /* ignore */
                } else if (d >= -1) {
                    link += text[ix];
                } else {
                    throw 'ruh roh!';
                }
            } else if (d == null) {
                if (c >= -1) {
                    chain.push('<p>');
                    if (c >= 0) {
                        chain.push(fragment_open_tag(c));
                        chain.push(fragment_firstchar(text[ix]));
                    } else {
                        chain.push(text[ix]);
                    }
                }
            } else {
                chain.push(link);
                link = '';

                if ((c == -1) && (d == -2)) {
                    // From a break to normal text
                    chain.push('<p>');
                    link += text[ix];
                } else if ((c == -1) && (d >= 0)) {
                    // From normal text to fragment text
                    chain.push(chain.pop().slice(0, -1));
                    chain.push(fragment_lastchar(text[ix-1]));
                    chain.push(fragment_close_tag());
                    link += text[ix];
                } else if ((c >= 0) && ((d == -2) || (d == -1))) {
                    // From a break or normal text to a fragment
                    if (d == -2) {
                        chain.push('<p>');
                    }
                    chain.push(fragment_open_tag(c));
                    chain.push(fragment_firstchar(text[ix]));
                } else if ((c >= 0) && (d >= 0)) {
                    // From one fragment to another fragment
                    chain.push(chain.pop().slice(0, -1));
                    chain.push(fragment_lastchar(text[ix-1]));
                    chain.push(fragment_close_tag());
                    chain.push(fragment_open_tag(c));
                    chain.push(fragment_firstchar(text[ix]));
                } else if ((c == -2) && (d == -1)) {
                    // From normal text to a break
                    chain.push('</p>');
                } else if ((c == -2) && (d >= 0)) {
                    // From a fragment to a break
                    chain.push(chain.pop().slice(0, -1));
                    chain.push(fragment_lastchar(text[ix-1]));
                    chain.push(fragment_close_tag());
                    chain.push('</p>');
                }
            }

            d = c;
        }
        chain.push(link);
        if ((link.length >= 4) && (link.slice(-4) != '</p>')) {
            chain.push('</p>');
        }
        return chain.join('');
    };

    window.highlight_fragments = function (lefttext, righttext, fragments) {
        var leftbitmap = new Array(lefttext.length);
        var rightbitmap = new Array(righttext.length);

        for (var ix = 0; ix < leftbitmap.length; ix++) {
            leftbitmap[ix] = -1;
        }

        for (var ix = 0; ix < rightbitmap.length; ix++) {
            rightbitmap[ix] = -1;
        }

        for (var ix = 0; ix < fragments.length; ix++) {
            var frag = fragments[ix];
            for (var x = frag[0]; x < frag[0] + frag[2]; x++) {
                leftbitmap[x] = ix;
            }
            for (var x = frag[1]; x < frag[1] + frag[2]; x++) {
                rightbitmap[x] = ix;
            }
        }

        mark_blank_lines(lefttext, leftbitmap);
        mark_blank_lines(righttext, rightbitmap);

        mark_paragraph_breaks(lefttext, leftbitmap);
        mark_paragraph_breaks(righttext, rightbitmap);

        return [rewrite_text(lefttext, leftbitmap),
                rewrite_text(righttext, rightbitmap)];
    };

})();
