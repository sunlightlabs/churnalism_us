(function($){
    $(document).ready(function(){
        var short_number = function (n) {
            var sizes = [
                ['T', Math.pow(10, 12)],
                ['bn', Math.pow(10, 9)],
                ['M', Math.pow(10, 6)],
                ['k', Math.pow(10, 3)]
            ];
            for (var ix = 0; ix < sizes.length; ix++) {
                var label = sizes[ix][0];
                var threshold = sizes[ix][1];
                if (n >= threshold) {
                    var short_n = Math.round(n / threshold, 2);
                    return short_n.toString() + label;
                }
            }
            return n;
        };

        var match_curve_histo_url = function (doc_type) {
            var url = jQuery("link#match-curve-histogram").attr('href') + "?doc_type=";
            doc_type = parseInt(doc_type);
            if (isNaN(doc_type)) {
                return url;
            } else {
                return url + doc_type.toString();
            }
        };

        var show_doc_type_histogram = function (doc_type) {
            jQuery('#match-curve-histo svg').remove();
            show_histogram(match_curve_histo_url(doc_type),
                           "#match-curve-histo",
                           {
                               'normalization': 'denormalized',
                               'bar_padding': 1,
                               'mass_format': short_number,
                           });
            jQuery('select#doc-type').val(doc_type ? doc_type.toString() : 'None');
        };

        show_doc_type_histogram(sel_doc_type);
        show_histogram(jQuery("link#match-overlap-pct-histogram").attr("href"),
                       "#match-overlap-pct-histo",
                       {
                           'normalization': 'denormalized',
                           'bar_padding': 1,
                           'mass_format': short_number,
                           'height': 300
                       });
        show_histogram(jQuery("link#match-overlap-chars-histogram").attr("href"),
                       "#match-overlap-chars-histo",
                       {
                           'normalization': 'denormalized',
                           'bar_padding': 1,
                           'mass_format': short_number,
                           'height': 300
                       });

        jQuery("select#doc-type").change(function(event){
            var doc_type = parseInt(jQuery(this).val());

            show_doc_type_histogram(doc_type);
            if (history && history.pushState) {
                var dashboard_url = jQuery("link#match-dashboard").attr('href');
                if (isNaN(doc_type) === false) {
                    dashboard_url = dashboard_url + doc_type.toString() + '/';
                }
                history.pushState({doc_type: doc_type},
                                  null,
                                  dashboard_url);
            }
        });

        jQuery(window).on('popstate', function(event){
            if (event.originalEvent && event.originalEvent.state) {
                show_doc_type_histogram(event.originalEvent.state.doc_type);
            }
        });
    });
})(jQuery);

