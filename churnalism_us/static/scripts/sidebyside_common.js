(function(window){
    // Patch some built-in prototypes to simulate Javascript 1.8 in older browsers.

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


    // Begin Churnalism-centric code

    // This is for adding formatting to the document text to allow for CSS styling, etc.
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

    if (window.jQuery) {
        window.jQuery.fn.extend({
            markupAsArticle: function (){
                // The assumption here is that the html is just text
                // so .html() and .text() each achieve the correct outcome
                // with correct usage of this function while .html() is less
                // correct but fails more gracefully with incorrect usage of
                // this function.
                var txt = jQuery(this).html();
                var markup = markup_text(txt);
                jQuery(this).html(markup);
                return this;
            }
        });

        window.jQuery.fn.extend({
            pruneToHeight: function (height, more_text, less_text) {
                var more_text = more_text || '[show]';
                var less_text = less_text || '[hide]';

                var shortened = this[0].cloneNode(true); // Save a reference to the original DOM
                var $shortened = jQuery(shortened);
                var original = this[0].cloneNode(true);
                var $original = jQuery(original);
                $original.hide();

                var $container = jQuery('<div class="condense_control_container"></div>');
                jQuery(this[0]).replaceWith($container);
                $container.append($shortened);
                $container.append($original);

                var chopping_block = $shortened.find('*').toArray();
                while ((chopping_block.length > 1) && ($shortened.height() > height)) {
                    jQuery(chopping_block.pop()).remove();
                }

                var $more = jQuery('<span class="condense_control condense_control_more"></span>');
                $more.text(more_text);
                $more.click(function(){
                    $shortened.hide();
                    $original.show();
                });

                var $less = jQuery('<span class="condense_control condense_control_less"></span>');
                $less.text(less_text);
                $less.click(function(){
                    $original.hide();
                    $shortened.show();
                    $shortened.find('.condense_control')[0].scrollIntoView(false);
                });

                $shortened.append($more);
                $original.append($less);

                return this;
            }
        });
    }

})(window);

