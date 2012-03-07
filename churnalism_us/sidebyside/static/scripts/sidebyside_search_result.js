$(document).ready(function(){
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
                var sub_snippets = snippet.split(/[\r\n]+/).map(function(ss){ return ss.trim(); });
                $.each(sub_snippets, function(idx, sub_snippet){
                    if (sub_snippet.length > 0) {
                        highlight_match(match_text_el(doctype, docid), sub_snippet);
                    }
                });
            });
        });
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

