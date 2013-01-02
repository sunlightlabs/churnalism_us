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

String.prototype.trimRight = function() {
    return this.replace(/\s+$/,'');
}

ArticleExtractor = function (NS, loglevel) {
    var log = new LogWrapper(loglevel || LogWrapper.NOTICE);
    var jQuery = NS.jQuery || jQuery;
    var $ = NS.$ || $;

    var MIN_LEN = 25;

    var htmlElements = /^(a|abbr|address|area|article|aside|audio|b|base|bdi|bdo|blockquote|body|br|button|canvas|caption|cite|code|col|colgroup|command|datalist|dd|del|details|dfn|div|dl|dt|em|embed|fieldset|figcaption|figure|footer|form|h1|h2|h3|h4|h5|h6|head|header|hgroup|hr|html|i|iframe|img|input|ins|kbd|keygen|label|legend|li|link|map|mark|menu|meta|meter|nav|noscript|object|ol|optgroup|option|output|p|param|pre|progress|q|rp|rt|ruby|s|samp|script|section|select|small|source|span|strong|style|sub|summary|sup|table|tbody|td|textarea|tfoot|th|thead|time|title|tr|track|u|ul|var|video|wbr)$/i;
    var unlikelyCandidates = /ie6nomore|combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter|slideshow|imgfull|image|thumb|timestamp|hidden/i;
    var okMaybeItsACandidate = /and|article|body|content|story|column|main|shadow/i;
    var classWeightPositive = /article|body|content|entry|hentry|main|page|pagination|post|\btext\b|blog|story/i;
    var classWeightNegative = /combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget|hidden/i;
    var divToPElements = /<(a|blockquote|dl|div|img|ol|p|pre|table|ul)/i;
    var blacklistedSelectors = ['#ad_leaderboard_flex',
                                '#logo',
                                '#top_nav',
                                '#topnav',
                                '#around_the_web',
                                '#sidebar_right',
                                '#ad_bottom_article_text',
                                '#threeup_top_wrapper',
                                '#twitter_module_wrapper',
                                '.promo_holder',
                                '.comments_block_holder'];

    // Many news sites are bifurcated at a very high level. We can use this to
    // our advantage to focus on the area most likely to contain the article.
    // To do so we apply a series of selectors. The first element to match the
    // selector and be the only match becomes the focus of all further analysis.
    // Since the first matching selector is used, these must be very accurate
    // and the order matters!
    var quickTargetSelectors = ['div#article',
                                'div.articleBody',
                                'div.yog-col.yom-primary.yog-16u'];

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

    var node_desc = function (node) {
        var rope = [node.tagName];
        if (node.id) {
            rope.push('#');
            rope.push(node.id);
        }

        if (jQuery(node).attr('class') != null) {
            var clsArray = new Array(node.classList);
            rope.push('.');
            rope.push(clsArray.join('.'));
        }

        return rope.join('');
    };

    var remove_elements = function (elems) {
        log.debug('Removing', elems.length, 'elements');
        if (elems != null) {
            for (var idx = 0; idx < elems.length; idx++) {
                var el = elems[idx];
                if ((el.parentNode !== null) && (el.parentNode.parentNode !== null)) {
                    log.debug('Removed', node_desc(el));
                    if (el.parentNode.childNodes.length == 1) {
                        el.parentNode.parentNode.removeChild(el.parentNode);
                    } else {
                        el.parentNode.removeChild(el);
                    }
                }
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

    var ExtractedDocument = function (source_document) {
        var that = this;

        var doc = source_document.implementation.createHTMLDocument(document.title);
        doc.documentElement.appendChild(source_document.head.cloneNode(true));
        doc.documentElement.appendChild(source_document.body.cloneNode(true));

        var manip_target = null;
        var best_candidate = null;
        var article_elem = null;
        var title = null;

        var textRenderer = function (root) {
            var walker = doc.createTreeWalker(
                root,
                (NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT |
                NodeFilter.SHOW_ENTITY | NodeFilter.SHOW_ENTITY_REFERENCE),
                function(node){
                    if (node.nodeType == 3) {
                        return NodeFilter.FILTER_ACCEPT;
                    } else if (/^(p|br|pre|h\d)$/i.test(node.nodeName)) {
                        return NodeFilter.FILTER_ACCEPT;
                    } else if (node.nodeName == "SCRIPT") {
                        return NodeFilter.FILTER_REJECT;
                    } else {
                        return NodeFilter.FILTER_SKIP;
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
                } else if (/^(p|br|pre|h\d)$/i.test(walker.currentNode.nodeName)) {
                    rope.push(' \n');
                } else {
                    log.debug('ArticleExtractor ignoring node: ' + walker.currentNode.nodeType + ' (' + walker.currentNode.nodeName + ')');
                }
            }

            return rope.join('')
                       .replace(/^\s+$/m, '')                           // Kill empty lines
                       .replace(/[\r\n]{2,}/g, '\n')                    // Collapse 2+ line breaks into a single line break
                       .replace(/\n/g, '\n\n')                          // Re-expand line breaks to 2-breaks for readability
                       .replace(/ ([.,;:]\s)/g, '$1')
                       .replace(/([[{(]) (.+) ([)}\]])/g, '$1$2$3');
        };

        var quick_target = function () {
            var n_selectors = quickTargetSelectors.length;
            for (var ix = 0; ix < n_selectors; ix++) {
                var sel = quickTargetSelectors[ix];
                var $target = jQuery(sel, doc);
                if ($target.length == 1) {
                    remove_elements($target.siblings());
                    manip_target = $target[0].parentNode;
                    log.debug("USING QUICK TARGET SELECTOR:", sel);
                    return;
                }
            }
            log.debug("NOT USING QUICK TARGET");
            manip_target = doc.documentElement;
        };

        var fix_misused_divs = function () {
            var _fix_div = function (div) {
                var p = doc.createElement('p');
                p.innerHTML = div.innerHTML;
                var $p = jQuery(p);
                var $div = jQuery(div);
                $p.attr('id', $div.attr('id'));
                $p.attr('class', $div.attr('class'));
                div.parentNode.replaceChild(p, div);
            };
            var divs = jQuery('div', manip_target).toArray();
            divs.forEach(function(div){
                var $div = jQuery(div);
                if ($div.css('display') == 'inline') {
                    _fix_div(div);
                } else {
                    var match_offset = div.innerHTML.search(divToPElements);
                    if (match_offset === -1) {
                        _fix_div(div);
                    }
                }
            });
            // Omitted a readability logic block marked experimental
        };

        var remove_unlikely_candidates = function () {
            var remove_schedule = [];

            var node_is_unlikely = function (node) {
                var $node = jQuery(node);
                var class_attr = $node.attr('class');
                var id_attr = $node.attr('id');
                var class_str = '';
                var id_str = '';
                if (class_attr !== undefined) {
                    class_str = class_attr.toString();
                    if (class_str.search(okMaybeItsACandidate) >=0) {
                        return false;
                    }
                }
                if (id_attr !== undefined) {
                    id_str = id_attr.toString();
                    if (id_str.search(okMaybeItsACandidate) >= 0) {
                        return false;
                    }
                }
                if (node.tagName === 'BODY') {
                    return false;
                }
                if (class_str.search(unlikelyCandidates) >= 0) {
                    return true;
                }
                if (id_str.search(unlikelyCandidates) >= 0) {
                    return true;
                }
                return false;
            };

            var accept_unlikely = function (node) {
                var is_unlikely = node_is_unlikely(node);
                return (is_unlikely === true)
                       ? NodeFilter.FILTER_ACCEPT
                       : NodeFilter.FILTER_SKIP;
            };

            var walker = null;
            walker = doc.createTreeWalker(manip_target,
                                          NodeFilter.SHOW_ELEMENT,
                                          accept_unlikely,
                                          false);

            while (walker.nextNode()) {
                remove_schedule.push(walker.currentNode);
                log.debug('ArticleExtractor', walker.currentNode.tagName, walker.currentNode.nodeType);
            }
            remove_elements(remove_schedule);
        };

        var default_score = function (node) {
            switch (node.tagName) {
                case 'ARTICLE':
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
            var $node = jQuery(node);
            var classstr = $node.attr('class');
            var idstr = $node.attr('id');
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

                var grandparent_node = parent_node.parentNode;
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

            // Incuding DIVs here is a little lax but our ability to detect DIVs that
            // are used like Ps is hampered, mostly by the UL element. We just have to
            // rely on the lower rank of DIV vs P.
            jQuery("P, PRE, TD, FORM, ARTICLE, DIV", manip_target).each(function(idx, node){ scorer(node); });

            jQuery("*", manip_target).each(function(idx, node){
                if (node.extractionScore == null)
                    return;
                node.extractionScore *= (1 - link_density(node));

                if (((best_candidate == null) && (node.extractionScore != null)) || (node.extractionScore >= best_candidate.extractionScore)) {
                    log.info('best candidate, with score', node.extractionScore, ' is now ', node_desc(node));
                    best_candidate = node;
                }
            });
            if (best_candidate == null) {
                log.notice('No article content found.');
                throw 'ArticleExtractor: No article content found.';
            }
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
            article_elem = doc.createElement('ARTICLE');
            var sibling_threshold = Math.max(10, best_candidate.extractionScore * 0.2);
            jQuery(best_candidate.parentNode.childNodes).each(function(idx, sibling){
                var append_flag = false;
                if (sibling.nodeType == Node.COMMENT_NODE)
                    return;

                if (sibling == best_candidate)
                    append_flag = true;

                if ((best_candidate.className != null) && (sibling.className == best_candidate.className))
                    append_flag = true;

                if (sibling.extractionScore >= sibling_threshold) 
                    append_flag = true;

                if ((sibling.tagName === 'P') || (htmlElements.test(sibling.tagName) == false)) {
                    var sibling_link_density = link_density(sibling);
                    var sibling_content = clean(sibling.textContent);
                    if ((sibling_content.length > 80) && (sibling_link_density < 0.25))
                        append_flag = true;
                    else if ((sibling_content.length < 80) && /\.( |jQuery)/.test(sibling_content))
                        append_flag = true;
                }

                if (append_flag == true) {
                    if (sibling !== best_candidate) {
                        log.info('Appending sibling', sibling.tagName, 'with score', sibling.extractionScore, node_desc(sibling), sibling);
                    }
                    article_elem.appendChild(sibling);
                    article_elem.appendChild(doc.createTextNode('\n'));
                }
            });
        };

        var sanitize_article = function () {
            remove_elements(jQuery('object, embed', article_elem));

            jQuery("*", article_elem).each(function(idx, node){
                var $node = jQuery(node);

                if (/h\d/i.test(node.tagName)) {
                    if ((class_score(node) < 0) || (link_density(node) > 0.33)) {
                        jQuery(node).remove();
                        return;
                    }
                }

                // The remove_unlikely_candidates function removes most image insets.
                // This targets those missed by remove_unlikely_candidates.
                if (/(img|object|embed)/i.test(node.tagName) && (node.parentNode !== null) && (node.parentNode.textContent.length < 180)) {
                    jQuery(node.parentNode).remove();
                    return;
                }

                if (/form/i.test(node.tagName)) {
                    // Ideally we would just remove all form elements.
                    // Unfortunately there are sites that use forms
                    // to hide content from IE6.
                    if ($node.text().length < 900) {
                        $node.remove();
                        return;
                    }
                }

                if (/ul|ol/i.test(node.tagName)) {
                    if ($node.parents().toArray().indexOf(best_candidate) == -1) {
                        $node.remove();
                        return
                    }
                }

                if ((node.tagName == 'A') && (node.parentNode != null) && (node.parentNode.tagName == 'LI')) {
                    $node.remove();
                    return;
                }

                if (/table/i.test(node.tagName)) {
                    var chars_per_cell = clean(node.textContent).length / jQuery('TD', node).length;
                    if (chars_per_cell < 15) {
                        jQuery('TR', node).each(function(idx, tr){
                            var tr_text = jQuery('td', tr).map(function(idx, cell){
                                return clean(cell.textContent);
                            }).toArray().join(' | ');
                            var span = doc.createElement('SPAN');
                            span.innerText = tr_text;
                            jQuery(span).append(doc.createElement('BR'));
                            jQuery(tr).replaceWith(span);
                        });
                        return;
                    }
                }

                if (/p/i.test(node.tagName)) {
                    var density = link_density(node);
                    if (density > 0.85) {
                        log.info('Link density of ' + density + ' for: ' + node.textContent);
                        $node.remove();
                        return;
                    }
                }

                if (/table|ul|ol|div|form/i.test(node.tagName)) {
                    var content_score = (node.extractionScore == null) ? 0 : node.extractionScore;
                    var cls_score = class_score(node);
                    if ((cls_score + content_score) < 0) {
                        $node.remove();
                    } else if (node.textContent.split(',').length - 1 < 10) {
                        var p_cnt = jQuery("p", node).length;
                        var img_cnt = jQuery("img", node).length;
                        var li_cnt = jQuery("li", node).length - 100;
                        var input_cnt = jQuery("input", node).length;

                        if (img_cnt > p_cnt) {
                            $node.remove();
                        } else if ((li_cnt > p_cnt) && (node.tagName != 'ul') && (node.tagName != 'ol')) {
                            $node.remove();
                        } else if (input_cnt > Math.floor(p_cnt / 3)) {
                            $node.remove();
                        } else if (text_length(node) < 25) {
                            if (text_length(node.parentNode) < 35) {
                                $node.parent().remove();
                            } else {
                                $node.remove();
                            }
                        } else {
                            var lnk_density = link_density(node);
                            if ((node.extractionScore < 25) && (lnk_density > 0.2)) {
                                $node.remove();
                            } else if ((node.extractionScore >= 25) && (lnk_density > 0.5)) {
                                $node.remove();
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

            if (doc.title !== undefined) {
                title = doc.title.trim();
                if (title.length > 0)
                    return;
            }
        };

        var sanitize_title = function () { 
            if (title !== undefined) {
                var headers = jQuery('h1').toArray();
                for (var idx = 0; idx < headers.length; idx++) {
                    var hdrtext = jQuery(headers[idx]).text().trim();
                    if (title.indexOf(hdrtext) >= 0) {
                        title = hdrtext;
                        return;
                    }
                } 
            }
        };

        quick_target();
        log.debug('MANIPULATION TARGET:', node_desc(manip_target));
        log.debug('HTML:', doc.innerHTML);
        remove_elements(jQuery('script, noscript, style, iframe', manip_target));
        remove_elements(jQuery('textarea, select, option, button', manip_target));
        remove_elements(jQuery(blacklistedSelectors.join(', '), manip_target));
        // Remove hidden elements
        jQuery(manip_target).remove('*:hidden');
        remove_unlikely_candidates();
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
            return textRenderer(article_elem).replace(/[\t \xa0\u00a0]{2,}/g, ' ');
        };

        that.get_title = function () {
            return title;
        };

        return that;
    };

    NS.ExtractedDocument = ExtractedDocument;
};


