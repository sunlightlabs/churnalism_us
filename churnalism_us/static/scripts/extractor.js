/* Sites that pose problems:
 * 
 * Photo caption is included in article text:
 * http://www.latimes.com/health/la-sci-bird-flu-lethal-20120224,0,1494616.story
 * http://hayandforage.com/corn/industry-news-drought-tolerant-corn-hybrids-unveiled
 * http://www.acga.org/index.php?option=com_content&task=view&id=170&Itemid=42
 * http://gk.ph.gameclub.com/news/news_view.asp?bserial=1&idx=100
 *
 *
 */
var textRenderer = function (node) {
    var walker = document.createTreeWalker(
        node, 
        (NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT | 
        NodeFilter.SHOW_ENTITY | NodeFilter.SHOW_ENTITY_REFERENCE), 
        { 
            acceptNode: function(node){
                if (node.nodeType == 3) {
                    return NodeFilter.FILTER_ACCEPT; 
				} else if (/^(p|br|pre)$/i.test(node.nodeName)) {
					return NodeFilter.FILTER_ACCEPT;
				} else if (node.nodeName == "SCRIPT") {
					return NodeFilter.FILTER_REJECT;
                } else {
                    return NodeFilter.FILTER_SKIP;
                }
            } 
        }, 
        false
    );

	var rope = [];
    while (walker.nextNode()) {
        if (walker.currentNode.nodeType == 3) {
            var text = walker.currentNode.textContent.replace(/[ \t\s\r\n]+/g, ' ');
            var trimmed = text.trimRight();
            if (text != trimmed) {
                text = trimmed + ' ';
            } else {
                text = trimmed;
            }
            if (text.length > 0) {
				rope.push(text);
			}
		} else if (/^(p|br|pre)$/i.test(walker.currentNode.nodeName)) {
			rope.push(' \n');
        } else {
            console.log('ArticleExtractor ignoring node: ' + walker.currentNode.nodeType + ' (' + walker.currentNode.nodeName + ')');
		}
    }

	return rope.join('')
               .replace(/^\s+$/m, '')                           // Kill empty lines
               .replace(/[\r\n]{2,}/g, '\n')                    // Collapse 2+ line breaks into a single line break
               .replace(/\n/g, '\n\n')                          // Re-expand line breaks to 2-breaks for readability
               .replace(/ ([.,;:]\s)/g, '$1')
               .replace(/([[{(]) (.+) ([)}\]])/g, '$1$2$3');
};

ArticleExtractor = function (NS) {

    var MIN_LEN = 25;

    var htmlElements = /^(a|abbr|address|area|article|aside|audio|b|base|bdi|bdo|blockquote|body|br|button|canvas|caption|cite|code|col|colgroup|command|datalist|dd|del|details|dfn|div|dl|dt|em|embed|fieldset|figcaption|figure|footer|form|h1, h2, h3, h4, h5, h6|head|header|hgroup|hr|html|i|iframe|img|input|ins|kbd|keygen|label|legend|li|link|map|mark|menu|meta|meter|nav|noscript|object|ol|optgroup|option|output|p|param|pre|progress|q|rp|rt|ruby|s|samp|script|section|select|small|source|span|strong|style|sub|summary|sup|table|tbody|td|textarea|tfoot|th|thead|time|title|tr|track|u|ul|var|video|wbr)$/i;
    var unlikelyCandidates = /ie6nomore|combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter/i;
    var okMaybeItsACandidate = /and|article|body|column|main|shadow/i;
    var classWeightPositive = /article|body|content|entry|hentry|main|page|pagination|post|\btext\b|blog|story/i;
    var classWeightNegative = /combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget|hidden/i;
    var divToPElements = /<(a|blockquote|dl|div|img|ol|p|pre|table|ul)/i;

    var _describe = function (node, depth) {
        var name = node.tagName;

        var idstr = jQuery(node).attr('id');
        if ((idstr != null) && (idstr.length > 0))
            name = name + '#' + idstr;

        var classstr = jQuery(node).attr('class');
        if ((classstr != null) && (classstr.length > 0))
            name = name + '.' + classstr.replace(' ', '.');

        if (name != null) {
            var nameprefix = name.substr(0, 4);
            if ((nameprefix == 'div#') || (nameprefix == 'div.'))
                name = name.substr(3);
        }

        if ((depth > 0) && (node.parentNode != null))
            return name + ' - ' + describe(node.parentNode, depth - 1);

        return name;
    };

    var describe = function (node) {
        return _describe(node, 1);
    };

    var to_integer = function (str) {
        var str1 = str.strip();
        var suffix = str1.substr(-2);
        if (suffix == 'px')
            return parseInt(str1.slice(0, -2));
        if (suffix == 'em')
            return parseInt(str1.slice(0, -2)) * 12;
        return parseInt(str1);
    };

    var clean = function (text) {
        var re1 = /\s*\n\s*/g;
        var re2 = /[ \t]{2,}/g;
        return text.replace(re1, '\n').replace(re2, ' ');
    };

    var text_length = function (node) {
        return clean(node.textContent).length;
    };

    var remove_elements = function (elems) {
        if (elems != null) {
            for (var idx = 0; idx < elems.length; idx++) {
                var el = elems[idx];
                el.parentNode.removeChild(el);
            }
        }
    };

    var to_string = function (node) {
        var str = node.innerText;
        if ((node.nextSibling != null) && (node.nextSibling.nodeName == '#text')) {
            str += node.nextSibling.textContent;
        }
        return str;
    };

    var ExtractedDocument = function (srcdoc) {
        var that = this;
        var srcdoc = srcdoc; // Do not touch -- just for calling .createElement()
        var doc = srcdoc.documentElement.cloneNode(true);
        var best_candidate = null;
        var article_elem = null;
        var title = null;

        var fix_misused_divs = function () {
            var _fix_div = function (div) {
                var p = srcdoc.createElement('p');
                p.innerHTML = div.innerHTML;
                jQuery(p).attr('id', jQuery(div).attr('id'));
                jQuery(p).attr('class', jQuery(div).attr('class'));
            };
            jQuery('div').each(function(idx, div){
                if (jQuery(div).css('display') == 'inline') {
                    _fix_div(div);
                } else {
                    var childrenstr = jQuery.map(div.childNodes, to_string).join('');
                    if (! divToPElements.test(childrenstr)) {
                        _fix_div(div);
                    }
                }
            });
            // Omitted a readability logic block marked experimental
        };

        var remove_unlikely_candidates = function () {
            jQuery("*", doc).each(function(idx, node){
                var attrstr = jQuery(node).attr('class') + ' ' + jQuery(node).attr('id');
                if ((attrstr.search(unlikelyCandidates) >= 0)
                    && (attrstr.search(okMaybeItsACandidate) == -1)
                    && (node.tagName != 'BODY')) {
                    jQuery(node).remove();
                }
            });
        };

        var default_score = function (node) {
            switch (node.tagName) {
                case 'DIV':
                    return 5;

                case 'PRE':
                case 'TD':
                case 'BLOCKQUOTE':
                    return 3;

                case 'ADDRESS':
                case 'OL':
                case 'UL':
                case 'DL':
                case 'DD':
                case 'DT':
                case 'LI':
                    return -3;

                case 'H1':
                case 'H2':
                case 'H3':
                case 'H4':
                case 'H5':
                case 'H6':
                case 'TH':
                    return -5;

                default:
                    return 0;
            };
        };

        var class_score = function (node) {
            var classstr = jQuery(node).attr('class');
            var idstr = jQuery(node).attr('id');
            var score = 0;

            if ((classstr != null) && (classstr.length > 0)) {
                if (classstr.search(classWeightNegative) >= 0)  {
                    score -= 25;
                }
                
                if (classstr.search(classWeightPositive) >= 0) {
                    score += 25;
                }
            }

            if ((idstr != null) && (idstr.length > 0)) {
                if (idstr.search(classWeightNegative) >= 0) {
                    score -= 25;
                }

                if (idstr.search(classWeightPositive) >= 0) {
                    score += 25;
                }
            }

            return score;
        };

        var score_node = function (node) {
            var def = default_score(node);
            var cls = class_score(node);
            node.extractionScore = def + cls;
        };

        var score_paragraphs = function () {
            var MIN_LEN = 25;
            var candidates = [];
            var ordered = [];

            var scorer = function (node) {
                var parent_node = node.parentNode;
                if (parent_node == null)
                    return;

                var grandparent_node = node.parentNode.parentNode;
                if (grandparent_node == null)
                    return;

                var text = clean(node.textContent);
                if (text.length < MIN_LEN)
                    return;

                if (parent_node.extractionScore == null)
                    score_node(parent_node);

                if (grandparent_node.extractionScore == null)
                    score_node(grandparent_node);

                var content_score = 1;
                content_score += text.split(',').length;
                content_score += text.split('"').length / 2;
                content_score += Math.min(text.length / 100, 3);
                parent_node.extractionScore += content_score;
                grandparent_node.extractionScore += (content_score / 2);
            };

            jQuery("P, PRE, TD, FORM", doc).each(function(idx, node){ scorer(node); });

            jQuery("*", doc).each(function(idx, node){
                if (node.extractionScore == null)
                    return;
                node.extractionScore *= (1 - link_density(node));

                if (((best_candidate == null) && (node.extractionScore != null)) || (node.extractionScore >= best_candidate.extractionScore)) {
                    console.log('best candidate, with score', node.extractionScore, ' is now ', node);
                    best_candidate = node;
                }
            });
            if (best_candidate == null) 
                throw 'ArticleExtractor: No candidate found!';
        };

        var link_density = function (node) {
            var len = 0;
            jQuery('a', node).each(function(idx, a){
                len += text_length(a);
            });
            if (len == 0) {
                return 0;
            } else {
                return len / Math.max(text_length(node), 1);
            }
        };

        var extract_article = function () {
            article_elem = srcdoc.createElement('ARTICLE');
            var sibling_threshold = Math.max(10, best_candidate.extractionScore * 0.2);
            jQuery(best_candidate.parentNode.childNodes).each(function(idx, sibling){
                var append_flag = false;
                if (sibling == best_candidate)
                    append_flag = true;

                if ((best_candidate.className != null) && (sibling.className == best_candidate.className))
                    append_flag = true;

                if (sibling.extractionScore >= sibling_threshold) 
                    append_flag = true;

                if ((sibling.tagName == 'P') || (htmlElements.test(sibling.tagName) == false)) {
                    var sibling_link_density = link_density(sibling);
                    var sibling_content = clean(sibling.textContent);
                    if ((sibling_content.length > 80) && (sibling_link_density < 0.25))
                        append_flag = true;
                    else if ((sibling_content.length < 80) && /\.( |jQuery)/.test(sibling_content))
                        append_flag = true;
                }

                if (append_flag == true) {
                    article_elem.appendChild(sibling);
                    article_elem.appendChild(srcdoc.createTextNode('\n'));
                }
            });
        };

        var sanitize_article = function () {
            remove_elements(jQuery('object, embed, iframe, noscript', article_elem));

            jQuery("*", article_elem).each(function(idx, node){
                if (/h\d/i.test(node.tagName)) {
                    if ((class_score(node) < 0) || (link_density(node) > 0.33)) {
                        jQuery(node).remove();
                        return;
                    }
                }

                if (/form/i.test(node.tagName)) {
                    // Ideally we would just remove all form elements.
                    // Unfortunately there are sites that use forms
                    // to hide content from IE6.
                    if (jQuery(node).text().length < 900) {
                        jQuery(node).remove();
                        return;
                    }
                }

                if (/ul|ol/i.test(node.tagName)) {
                    if (jQuery(node).parents().toArray().indexOf(best_candidate) == -1) {
                        jQuery(node).remove();
                        return
                    }
                }

                if ((node.tagName == 'A') && (node.parentNode != null) && (node.parentNode.tagName == 'LI')) {
                    jQuery(node).remove();
                    return;
                }

                if (/table/i.test(node.tagName)) {
                    var chars_per_cell = clean(node.textContent).length / jQuery('TD', node).length;
                    if (chars_per_cell < 15) {
                        jQuery('TR', node).each(function(idx, tr){
                            var tr_text = jQuery('td', tr).map(function(idx, cell){
                                return clean(cell.textContent);
                            }).toArray().join(' | ');
                            var span = srcdoc.createElement('SPAN');
                            span.innerText = tr_text;
                            jQuery(span).append(srcdoc.createElement('BR'));
                            jQuery(tr).replaceWith(span);
                        });
                        return;
                    }
                }

                if (/p/i.test(node.tagName)) {
                    var density = link_density(node);
                    if (density > 0.85) {
                        console.log('Link density of ' + density + ' for: ' + node.textContent);
                        jQuery(node).remove();
                        return;
                    }
                }

                if (/table|ul|ol|div|form/i.test(node.tagName)) {
                    var content_score = (node.extractionScore == null) ? 0 : node.extractionScore;
                    var cls_score = class_score(node);
                    if ((cls_score + content_score) < 0) {
                        jQuery(node).remove();
                    } else if (node.textContent.split(',').length - 1 < 10) {
                        var p_cnt = jQuery("p", node).length;
                        var img_cnt = jQuery("img", node).length;
                        var li_cnt = jQuery("li", node).length - 100;
                        var input_cnt = jQuery("input", node).length;

                        if (img_cnt > p_cnt) {
                            jQuery(node).remove();
                        } else if ((li_cnt > p_cnt) && (node.tagName != 'ul') && (node.tagName != 'ol')) {
                            jQuery(node).remove();
                        } else if (input_cnt > Math.floor(p_cnt / 3)) {
                            jQuery(node).remove();
                        } else if (text_length(node) < 25) {
                            if (text_length(node.parentNode) < 35) {
                                jQuery(node.parentNode).remove();
                            } else {
                                jQuery(node).remove();
                            }
                        } else {
                            var lnk_density = link_density(node);
                            if ((node.extractionScore < 25) && (lnk_density > 0.2)) {
                                jQuery(node).remove();
                            } else if ((node.extractionScore >= 25) && (lnk_density > 0.5)) {
                                jQuery(node).remove();
                            }
                        }
                    }
                }
            });
        };

        var extract_title = function () { 
            title = jQuery('#title', doc).text().trim();
            if (title.length > 0)
                return; 

            title = jQuery('h1', article_elem).text().trim();
            if (title.length > 0)
                return;

            title = jQuery('meta[name=Title]').attr('content');
            if ((title != null) && (title.length > 0))
                return;

            title = srcdoc.title.trim();
            if (title.length > 0)
                return;
        };

        var sanitize_title = function () { 
            var headers = jQuery('h1').toArray();
            for (var idx = 0; idx < headers.length; idx++) {
                var hdrtext = headers[idx].innerText.trim();
                if (title.indexOf(hdrtext) >= 0) {
                    title = hdrtext;
                    return;
                }
            } 
        };

        remove_elements(jQuery('script, noscript', doc));
        remove_elements(jQuery('style', doc));
        remove_elements(jQuery('textarea, select, option, button', doc));
        remove_unlikely_candidates();
        // Remove hidden elements
        jQuery(doc).remove('*:hidden, P:hidden, DIV:hidden, PRE:hidden, TD:hidden');
        fix_misused_divs();
        score_paragraphs();
        extract_article();
        sanitize_article();
        extract_title();
        sanitize_title();

        that.get_best_candidate = function () {
            return best_candidate;
        };

        that.get_article = function () {
            return article_elem;
        };

        that.get_article_text = function () {
            return textRenderer(article_elem);
        };

        that.get_title = function () {
            return title;
        };

        return that;
    };

    NS.ExtractedDocument = ExtractedDocument;
};

