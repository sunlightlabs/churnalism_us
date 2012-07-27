(function(){
    var elementInViewport = function (el) {
        var rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= window.innerHeight &&
            rect.right <= window.innerWidth
        );
    };

    var elementsOutsideViewport = function (els) {
        return els.filter(function(idx){
            return !elementInViewport(this);
        });
    };

    var top_of = function (elem) {
        return elem.offset().top;
    };
    var bottom_of = function (elem) {
        return elem.offset().top + elem.outerHeight();
    };
    var middle_of = function (elem) {
        return top_of(elem) + ((bottom_of(elem) - top_of(elem)) / 2);
    };
    var right_of = function (elem) {
        return elem.offset().left + elem.outerWidth();
    };
    var left_of = function (elem) {
        return elem.offset().left;
    };
    var frag_number_matcher = function (frag_number) {
        /* Useful for filtering jQuery elements */
        return function(){
            var f = $(this).attr('churnalism:fragment');
            return ((f != null) && (f == frag_number));
        };
    };
    var fragment_elements = function (frag_number, ancestor) {
        var context = ancestor || document;
        return $("span.churnalism-highlight", context).filter(frag_number_matcher(frag_number));
    };
    var draw_connector = function (source_elem, target_elem) {
        var higher_elem = (top_of(source_elem) <= top_of(target_elem)) ? source_elem : target_elem;
        var source_on_top = (top_of(source_elem) <= bottom_of(target_elem));
        var lower_elem = source_on_top ? target_elem : source_elem;

        var source_elem = source_on_top ? $(".churnalism-highlight-lastchar", source_elem) : $(".churnalism-highlight-firstchar", source_elem);
        var target_elem = source_on_top ? $(".churnalism-highlight-firstchar", target_elem) : $(".churnalism-highlight-lastchar", target_elem);

        var conn_top = top_of(higher_elem);
        var conn_height = (top_of(lower_elem) - top_of(higher_elem)) + lower_elem.outerHeight();
        if (conn_height < higher_elem.outerHeight())
            conn_height = higher_elem.outerHeight();
        if (conn_height < lower_elem.outerHeight())
            conn_height = lower_elem.outerHeight();
        var conn_left = source_on_top ? right_of(source_elem) - 3 : left_of(source_elem);
        var conn_right = source_on_top ? left_of(target_elem) : right_of(target_elem);
        var conn_width = conn_right - conn_left;

        var svg = $($("#connector-tmpl").html());
        svg.css('position', 'absolute');
        svg.css('z-index', '999999');
        svg.css('top', conn_top + 'px');
        svg.css('height', conn_height + 'px');
        svg.css('width', conn_width + 8 + 'px');
        svg.css('left', conn_left + 'px');
        svg.css('background-color', 'transparent');
        $("body").append(svg);

        $(window).resize(function(resize){
            var source_elem = $('#doc-text span.churnalism-highlight-selected span.churnalism-highlight-lastchar');
            var target_elem = $('#pr-text span.churnalism-highlight-selected span.churnalism-highlight-firstchar');
            var source_on_top = (top_of(source_elem) <= top_of(target_elem));
            var higher_elem = source_on_top ? source_elem : target_elem;
            var lower_elem = source_on_top ? target_elem : source_elem;
            svg.css('top', Math.min(top_of(source_elem), top_of(target_elem)));
            svg.css('left', right_of(source_elem));
            svg.css('z-index', '999999');
        });

        var localize_x = function (x) {
            return x - conn_left + 1;
        };
        var localize_y = function (y) {
            return y - conn_top;
        };

        // Define the points through which the bezier line will pass
        // Point A is always defined in terms of the source element while 
        // point E is always in terms of the target element. C is the mid-point.
        var STARTy = localize_y(source_on_top ? top_of(source_elem) : bottom_of(source_elem));
        var ENDy = localize_y(source_on_top ? bottom_of(target_elem) : top_of(target_elem));
        var Ax = localize_x(source_on_top ? right_of(source_elem) - 3 : left_of(source_elem));
        var Ay = localize_y(source_on_top ? bottom_of(source_elem) : top_of(source_elem));
        Ay = localize_y(bottom_of(source_elem));
        var Ex = localize_x(source_on_top ? left_of(target_elem) : right_of(target_elem));
        var Ey = localize_y(source_on_top ? top_of(target_elem) : bottom_of(target_elem));
        var Cx = Ax + ((Ex - Ax) / 2);
        var Cy = Ay + ((Ey - Ay) / 2);

        // B and D are control points. They are the mid-points of the boxes created by 
        // (A,C) and (C,E) so as to create shallow curves.
        var Bx = Ax;
        var By = Ay + ((Cy - Ay) / 2);
        var Dx = Ex;
        var Dy = Ey - ((Ey - Cy) / 2);

        $("#A", svg).attr('cx', Ax);
        $("#A", svg).attr('cy', Ay);
        $("#B", svg).attr('cx', Bx);
        $("#B", svg).attr('cy', By);
        $("#C", svg).attr('cx', Cx);
        $("#C", svg).attr('cy', Cy);
        $("#D", svg).attr('cx', Dx);
        $("#D", svg).attr('cy', Dy);
        $("#E", svg).attr('cx', Ex);
        $("#E", svg).attr('cy', Ey);

        var path_tmpl = 'MAx,Ay QBx,By Cx,Cy QDx,Dy Ex,Ey';
        var path = path_tmpl.replace('Ax', Ax)
                            .replace('Ay', Ay)
                            .replace('Bx', Bx)
                            .replace('By', By)
                            .replace('Cx', Cx)
                            .replace('Cy', Cy)
                            .replace('Dx', Dx)
                            .replace('Dy', Dy)
                            .replace('Ex', Ex)
                            .replace('Ey', Ey)
                            .replace('STARTy', STARTy)
                            .replace('ENDy', ENDy);
        $("#bezier", svg).attr('d', path);
    };
  
    var corresponding_fragment = function (a, bs) {
        return jQuery(bs).filter(function(){ return this.isEqualNode(a); });
    };

    var all_fragments_correspond = function (as, bs) {
        if (as.length != bs.length) {
            return false;
        }
        jQuery(as).each(function(ix, a){
            var found = corresponding_fragment(a, bs);
            if (found.length != 1) {
                return false;
            }
        });
        return true;
    };

    $(document).ready(function(){
        var doc_text = search_results.text;
        var highlighted = highlight_fragments(doc_text, match_text, search_results.documents.rows[0].fragments);
        $("#doc-text").html(highlighted[0]);
        $("#pr-text").html(highlighted[1]);

        $('.churnalism-highlight').hover(function(){
            var frag_number = $(this).attr('churnalism:fragment');
            var fragments = fragment_elements(frag_number);
            fragments.addClass('churnalism-highlight-pair');
        });
        $('.churnalism-highlight').mouseout(function(){
            var frag_number = $(this).attr('churnalism:fragment');
            var fragments = fragment_elements(frag_number);
            fragments.removeClass('churnalism-highlight-pair');
        });
        $('.churnalism-highlight').click(function(click){
            var frag_number = $(this).attr('churnalism:fragment');
            var source_fragments = fragment_elements(frag_number, "#doc-text");
            var target_fragments = fragment_elements(frag_number, "#pr-text");
            var was_selected = $(this).hasClass('churnalism-highlight-selected');
            if (! was_selected) {
                $('.churnalism-highlight').removeClass('churnalism-highlight-selected');
                $(".fragment-connector").remove();
                source_fragments.addClass('churnalism-highlight-selected');
                target_fragments.addClass('churnalism-highlight-selected');
                draw_connector(source_fragments, target_fragments);
                if (elementInViewport(this) == false) {
                    jQuery(this).scrollintoview({ duration: 'slow' });
                }
            } else if (click.ctrlKey == true) {
                $('.churnalism-highlight').removeClass('churnalism-highlight-selected');
                $(".fragment-connector").remove();
            } else {
                var other_fragments = ($(this).parent().parent().attr('id') == 'doc-text') ? target_fragments : source_fragments;
                var other_hidden_fragments = elementsOutsideViewport(other_fragments);
                other_hidden_fragments.first().scrollintoview({ duration: 'slow' });
            }
            click.preventDefault(true);
            click.stopPropagation(true);
            return false;
        });
        $('.churnalism-highlight').dblclick(function(dblclick){
            if (window.getSelection) {
                window.getSelection().removeAllRanges();
            } else if (document.selection && document.selection.empty) {
                document.selection.empty();
            }
            dblclick.preventDefault(true);
            dblclick.stopPropagation(true);
            return false;
        });
    });
})();
