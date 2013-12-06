var zip_arrays = function () {
    var args = [].slice.call(arguments);
    var longest = args.reduce(function(a,b){
        return a.length>b.length ? a : b
    }, []);

    return longest.map(function(_,i){
        return args.map(function(array){return array[i]})
    });
};

var transform = function () {
    if ((arguments.length === 0) || ((arguments.length === 1) && (arguments[0].length === 0))) {
        return "";
    }

    var transforms = ["scale", "translate", "matrix", "rotate", "skewX", "skewY"];
    var is_transform = function (s) {
        return transforms.indexOf(s) !== -1;
    };

    var ix = 0;
    var args = Array.apply(null, arguments);
    var arg_pairs = zip_arrays(args, args.slice(1));
    var rope = arg_pairs.map(function(pair){
        var curr = pair[0];
        var next = pair[1];

        if (curr === undefined)
            throw "undefined transform argument";

        if (is_transform(curr)) {
            if (is_transform(next) || (next === undefined)) {
                return [curr, "() "];
            } else {
                return [curr, "("];
            }
        } else {
            if (is_transform(next) || (next === undefined)) {
                return [curr.toString(), ") "];
            } else {
                return [curr.toString(), ","];
            }
        }
    });

    rope = rope.reduce(function(a, b) {
        return a.concat(b);
    });
    return rope.join("").trim();
};

var show_histogram = function (url, target, options) {

    var options = options || {};
    var normalization = options['normalization'] || 'none';
    var outer_width = options['width'] || parseInt(d3.select(target)
                                                     .style('width')
                                                     .replace(/[^\d]/g, ''));
    var outer_height = options['height'] || parseInt(d3.select(target)
                                                       .style('height')
                                                       .replace(/[^\d]/g, ''));
    var bar_padding = options['bar_padding'] || 1;

    d3.json(url, function (error, response) {
        if (error) return console.warn(error);

        data = response;

        histo_data = data.bins.map(function(b){
            var mass = null; 
            if ((normalization === 'denormalized') && (data.normalized === true)) {
                mass = b.mass * data.total_mass;
            } else if ((normalization === 'normalized') && (data.normalized === false)) {
                mass = b.mass / data.total_mass;
            } else {
                mass = b.mass;
            }
            
            return {
                'mass': mass,
                'label': b.label,
                'ordinal_position': b.ordinal_position
            };
        });

        var positions = data.bins.map(function(b){ return b.ordinal_position; });

        var format_mass = options['mass_format'] || d3.format(",.0f");

        var margin = { top: 40, right: 30, bottom: 45, left: 90 };
        var width = outer_width - margin.top - margin.bottom;
        var height = outer_height - margin.right - margin.left;

        x_scale = d3.scale.ordinal()
                              .domain(positions)
                              .rangeRoundBands([0, width]);

        var max_mass = d3.max(histo_data.map(function(b){ return b.mass; }));
        var y_scale = d3.scale.sqrt()
                              .domain([0, max_mass])
                              .range([height, 0]);

        var x_axis = d3.svg.axis()
                           .scale(x_scale)
                           .orient('bottom')
                           .tickValues(d3.range(0, histo_data.length))
                           .tickFormat(function(ix){ return histo_data[ix].label; });

        var y_axis = d3.svg.axis()
                           .scale(y_scale)
                           .orient('left');

        var svg = d3.select(target)
                    .append('svg')
                    .attr('width', width + margin.left + margin.right)
                    .attr('height', height + margin.top + margin.bottom)
                    .append('g')
                    .attr('transform', transform('translate', margin.left, margin.top));

        var bin0 = data.bins[0];
        var bin1 = data.bins[1];
        bar_width = 0;
        if (data.bins.length == 1) {
            bar_width = width;
        } else if (data.bins.length > 1) {
            bar_width = x_scale(bin1.ordinal_position) - x_scale(bin0.ordinal_position);
        }

        if (bar_width == 0) {
            svg.append('g')
               .attr('transform', transform('translate', width / 2, height / 2))
               .append('text')
               .attr('text-anchor', 'middle')
               .text('No data to display');
        } else {
            var bar = svg.selectAll('.bar')
                         .data(histo_data);

            bar.enter()
               .append('g')
               .attr('class', 'bar')
               .attr('transform', function(d){
                   return transform('translate', x_scale(d.ordinal_position), y_scale(d.mass));
               });

            bar.append('rect')
               .attr('x', 1)
               .attr('width', x_scale.rangeBand() - bar_padding)
               .attr('height', function(d){ return height - y_scale(d.mass); });

            bar.append('text')
               .attr('dy', '.75em')
               .attr('y', -15)
               .attr('x', (bar_width - bar_padding) / 2)
               .attr('text-anchor', 'middle')
               .text(function(d){ return format_mass(d.mass); });
        }

        svg.append('g')
           .attr('class', 'x axis')
           .attr('transform', transform('translate', 0, height))
           .call(x_axis);

        svg.append('g')
           .attr('class', 'y axis')
           .call(y_axis);

        if (data.bin_axis_label.length > 0) {
            svg.append('g')
               .attr('transform', transform('translate', width / 2, height + margin.bottom))
               .append('text')
               .attr('text-anchor', 'middle')
               .text(data.bin_axis_label);
        }

        if (data.mass_axis_label.length > 0) {
            svg.append('g')
               .attr('transform', transform('translate', 0, -margin.left,
                                            'rotate', 90, -margin.left, 0))
               .append('text')
               .attr('text-anchor', 'left')
               .text(data.mass_axis_label);
        }

        if (data.title.length > 0) {
            svg.append('g')
               .attr('transform', transform('translate', width / 2, -24))
               .append('text')
               .attr('text-anchor', 'middle')
               .text(data.title);
        }

    });

};

