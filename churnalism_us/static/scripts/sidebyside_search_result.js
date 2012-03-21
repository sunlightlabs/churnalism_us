$(document).ready(function(){
    // Production steps of ECMA-262, Edition 5, 15.4.4.19
    // Reference: http://es5.github.com/#x15.4.4.19
    if (!Array.prototype.map) {
        Array.prototype.map = function(callback, thisArg) {

            var T, A, k;

            if (this == null) {
                throw new TypeError(" this is null or not defined");
            }

            // 1. Let O be the result of calling ToObject passing the |this| value as the argument.
            var O = Object(this);

            // 2. Let lenValue be the result of calling the Get internal method of O with the argument "length".
            // 3. Let len be ToUint32(lenValue).
            var len = O.length >>> 0;

            // 4. If IsCallable(callback) is false, throw a TypeError exception.
            // See: http://es5.github.com/#x9.11
            if ({}.toString.call(callback) != "[object Function]") {
                throw new TypeError(callback + " is not a function");
            }

            // 5. If thisArg was supplied, let T be thisArg; else let T be undefined.
            if (thisArg) {
                T = thisArg;
            }

            // 6. Let A be a new array created as if by the expression new Array(len) where Array is
            // the standard built-in constructor with that name and len is the value of len.
            A = new Array(len);

            // 7. Let k be 0
            k = 0;

            // 8. Repeat, while k < len
            while(k < len) {

                var kValue, mappedValue;

                // a. Let Pk be ToString(k).
                //   This is implicit for LHS operands of the in operator
                // b. Let kPresent be the result of calling the HasProperty internal method of O with argument Pk.
                //   This step can be combined with c
                // c. If kPresent is true, then
                if (k in O) {

                    // i. Let kValue be the result of calling the Get internal method of O with argument Pk.
                    kValue = O[ k ];

                    // ii. Let mappedValue be the result of calling the Call internal method of callback
                    // with T as the this value and argument list containing kValue, k, and O.
                    mappedValue = callback.call(T, kValue, k, O);

                    // iii. Call the DefineOwnProperty internal method of A with arguments
                    // Pk, Property Descriptor {Value: mappedValue, Writable: true, Enumerable: true, Configurable: true},
                    // and false.

                    // In browsers that support Object.defineProperty, use the following:
                    // Object.defineProperty(A, Pk, { value: mappedValue, writable: true, enumerable: true, configurable: true });

                    // For best browser support, use the following:
                    A[ k ] = mappedValue;
                }
                // d. Increase k by 1.
                k++;
            }

            // 9. return A
            return A;
        };      
    }
    if (!Array.prototype.reduce) {
        Array.prototype.reduce = function reduce(accumulator){
            if (this===null || this===undefined) throw new TypeError("Object is null or undefined");
            var i = 0, l = this.length >> 0, curr;

            if(typeof accumulator !== "function") // ES5 : "If IsCallable(callbackfn) is false, throw a TypeError exception."
                throw new TypeError("First argument is not callable");

            if(arguments.length < 2) {
                if (l === 0) throw new TypeError("Array length is 0 and no second argument");
                curr = this[0];
                i = 1; // start accumulating at the second element
            }
            else
                curr = arguments[1];

            while (i < l) {
                if(i in this) curr = accumulator.call(undefined, curr, this[i], i, this);
                ++i;
            }

            return curr;
        };
    }

    var op_add = function (a, b) {
        return a + b;
    };

    var permalink_pattern = /([a-z0-9]{32})\/(\d+)\/(\d+)\//;

    var markup_text = function (txt) {
        var trimmed = txt.trim();
        var normalizedWhitespace = trimmed.replace(/^\s+$/gm, '');
        var hasConsecutiveLineBreaks = /[\r\n]{2,}/g.test(normalizedWhitespace);
        var lineBreakPatternText = '(\\r|\\n|\\r\\n|\\n\\r)';
        if (hasConsecutiveLineBreaks)
            lineBreakPatternText = lineBreakPatternText + '{2,}';
        var lineBreakPattern = new RegExp(lineBreakPatternText, "g");
        var withPTags = normalizedWhitespace.replace(lineBreakPattern, '</p>\n<p>');
        return '<p>' + withPTags + '</p>';
    };

    var fetch_document = function (doctype, docid, next) {
        var url = '/api/document/DOCTYPE/DOCID/'.replace('DOCTYPE', doctype).replace('DOCID', docid);
        $.get(url, {
            crossDomain: false,
            cache: true,
        }).success(function(resp){
            next(doctype, docid, resp); 
        });
    };

    var show_document_response = function (doctype, docid, document_response) {
        $("div.match-text:visible").hide();
        var title = document_response['title'];
        if (title != null) {
            $("header#match-title").text(title).show();
        } else {
            $("header#match-title:visible").hide();
        }

        var url = document_response['url'];
        if (url != null) {
            $("a.match-url").attr("href", url).text(url);
            $("header.match-url:hidden").show();
        } else {
            $("header.match-url:visible").hide();
        }

        textdiv = match_text_el(doctype, docid);
        textdiv.html(markup_text(document_response['text']));
        textdiv.show();
        $.each(search_results['documents']['rows'], function(idx, row){
            $.each(row['snippets'], function(idx, snippet){
                var sub_snippets = snippet.split(/[\r\n]+/g).map(function(ss){ return ss.trim(); });
                $.each(sub_snippets, function(idx, sub_snippet){
                    if (sub_snippet.length > 0) {
                        highlight_match(match_text_el(doctype, docid), sub_snippet);
                    }
                });
            });
        });
        textdiv.find('i:first').scrollintoview();
    };

    var select_document = function (doctype, docid) {
        fetch_document(doctype, docid, show_document_response);
        selected = {
            'doctype': doctype,
            'docid': docid
        };
    };

    var build_text_idstr = function (doctype, docid) {
        return 'match-text-DOCTYPE-DOCID'.replace('DOCTYPE', doctype).replace('DOCID', docid);
    };

    var build_listitem_idstr = function (doctype, docid) {
        return 'match-title-DOCTYPE-DOCID'.replace('DOCTYPE', doctype).replace('DOCID', docid);
    };

    var match_listitem_el = function (doctype, docid) {
        return $('li#' + build_listitem_idstr(doctype, docid));
    };

    var match_text_el = function (doctype, docid) {
        return $('div#' + build_text_idstr(doctype, docid));
    };

    var extract_document_attrs = function (idstr) {
        var pattern = /match-(title|text)-(\d+)-(\d+)/;
        var matches = pattern.exec(idstr);
        if (matches.length == 4) {
            return { doctype: matches[2], docid: matches[3] };
        } else {
            return null;
        }
    };

    $("ul#results-listing li").click(function(click){
        var idstr = $(click.currentTarget).attr('id');
        var docattrs = extract_document_attrs(idstr);
        if (docattrs) {
            select_document(docattrs['doctype'], docattrs['docid']);
        }
    });

    var permalink_matches = permalink_pattern.exec(window.location.pathname);
    if ((permalink_matches != null) && (permalink_matches.length == 4)) {
        var doctype = permalink_matches[2];
        var docid = permalink_matches[3];
        select_document(doctype, docid);
    }

    sourcediv = $("div#source-text");

    $('body').scroll(function(event){
        event.preventDefault();
    });
});

