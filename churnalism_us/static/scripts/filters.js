Filters = {};
Filters.getPixels = function(img) {
    var c,ctx;
    if (img.getContext) {
        c = img;
        try { ctx = c.getContext('2d'); } catch(e) {}
    }
    if (!ctx) {
        c = this.getCanvas(img.width, img.height);
        ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0);
    }
    return ctx.getImageData(0,0,c.width,c.height);
};

Filters.getCanvas = function(w,h) {
    var c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
};

Filters.filterCanvas = function (canvas, filter, args) {
    var ctx = canvas.getContext('2d');
    var pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
    var fullargs = [pixels];
    for (var idx = 0; idx < args.length; idx++) {
        fullargs.push(args[idx]);
    }
    pixels = filter.apply(filter, fullargs);
    ctx.putImageData(pixels, 0, 0);
};

Filters.filterImage = function(filter, image, var_args) {
    var args = [this.getPixels(image)];
    for (var i=2; i<arguments.length; i++) {
        args.push(arguments[i]);
    }
    return filter.apply(null, args);
};

Filters.grayscale = function(pixels, args) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        // CIE luminance for the RGB
        var v = 0.2126*r + 0.7152*g + 0.0722*b;
        d[i] = d[i+1] = d[i+2] = v
    }
    return pixels;
};

Filters.lineify = function (pixels, blend) {
    if ((blend < 0) || (blend > 1)) {
        throw new Exception("blend argument must be >= 0 and <= 1.");
    }
    var weightA = blend;
    var weightB = 1 - blend;
    var offset = 0;
    var x0 = null;
    var xN = null;
    for (var y = 0; y < pixels.height; y++) {
        x0 = null;
        xN = null;

        for (var x = 0; x < pixels.width; x++) {
            var r = pixels.data[offset];
            var g = pixels.data[offset+1];
            var b = pixels.data[offset+2];
            var a = pixels.data[offset+3];
            if (r + g + b + a > 0) {
                xN = x;
                if (x0 == null) {
                    x0 = x;
                }
            }
            offset += 4;
        }

        if ((x0 != null) && (xN != null)) {
            var offset0 = (y * (pixels.width * 4)) + (x0 * 4);
            var offsetN = (y * (pixels.width * 4)) + (xN * 4);

            var bright0 = pixels.data[offset0]
            + pixels.data[offset0+1]
            + pixels.data[offset0+2];
            var brightN = pixels.data[offsetN]
            + pixels.data[offsetN+1]
            + pixels.data[offsetN+2];
            var color_offset = (bright0 > brightN) ? offset0 : offsetN;
            var rA = pixels.data[color_offset];
            var gA = pixels.data[color_offset+1];
            var bA = pixels.data[color_offset+2];
            var aA = pixels.data[color_offset+3];

            var ln_offset = offset0;
            for (var x = x0; x < xN; x++) {
                rB = pixels.data[ln_offset];
                gB = pixels.data[ln_offset+1];
                bB = pixels.data[ln_offset+2];
                aB = pixels.data[ln_offset+3];

                pixels.data[ln_offset] = (rA * weightA) + (rB * weightB);
                pixels.data[ln_offset+1] = (gA * weightA) + (gB * weightB);
                pixels.data[ln_offset+2] = (bA * weightA) + (bB * weightB);
                pixels.data[ln_offset+3] = (aA * weightA) + (aB * weightB);

                ln_offset += 4;
            }
        }
    }
    return pixels;
};

Filters.brightness = function(pixels, adjustment) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        d[i] += adjustment;
        d[i+1] += adjustment;
        d[i+2] += adjustment;
    }
    return pixels;
};

Filters.threshold = function(pixels, threshold) {
    var d = pixels.data;
    for (var i=0; i<d.length; i+=4) {
        var r = d[i];
        var g = d[i+1];
        var b = d[i+2];
        var v = (0.2126*r + 0.7152*g + 0.0722*b >= threshold) ? 255 : 0;
        d[i] = d[i+1] = d[i+2] = v
    }
    return pixels;
};

Filters.tmpCanvas = document.createElement('canvas');
Filters.tmpCtx = Filters.tmpCanvas.getContext('2d');

Filters.createImageData = function(w,h) {
    return this.tmpCtx.createImageData(w,h);
};

Filters.convolute = function(pixels, weights, opaque) {
    var side = Math.round(Math.sqrt(weights.length));
    var halfSide = Math.floor(side/2);

    var src = pixels.data;
    var sw = pixels.width;
    var sh = pixels.height;

    var w = sw;
    var h = sh;
    var output = Filters.createImageData(w, h);
    var dst = output.data;

    var alphaFac = opaque ? 1 : 0;

    for (var y=0; y<h; y++) {
        for (var x=0; x<w; x++) {
            var sy = y;
            var sx = x;
            var dstOff = (y*w+x)*4;
            var r=0, g=0, b=0, a=0;
            for (var cy=0; cy<side; cy++) {
                for (var cx=0; cx<side; cx++) {
                    var scy = Math.min(sh-1, Math.max(0, sy + cy - halfSide));
                    var scx = Math.min(sw-1, Math.max(0, sx + cx - halfSide));
                    var srcOff = (scy*sw+scx)*4;
                    var wt = weights[cy*side+cx];
                    r += src[srcOff] * wt;
                    g += src[srcOff+1] * wt;
                    b += src[srcOff+2] * wt;
                    a += src[srcOff+3] * wt;
                }
            }
            dst[dstOff] = r;
            dst[dstOff+1] = g;
            dst[dstOff+2] = b;
            dst[dstOff+3] = a + alphaFac*(255-a);
        }
    }
    return output;
};

if (!window.Float32Array)
    Float32Array = Array;

Filters.convoluteFloat32 = function(pixels, weights, opaque) {
    var side = Math.round(Math.sqrt(weights.length));
    var halfSide = Math.floor(side/2);

    var src = pixels.data;
    var sw = pixels.width;
    var sh = pixels.height;

    var w = sw;
    var h = sh;
    var output = {
        width: w, height: h, data: new Float32Array(w*h*4)
    };
    var dst = output.data;

    var alphaFac = opaque ? 1 : 0;

    for (var y=0; y<h; y++) {
        for (var x=0; x<w; x++) {
            var sy = y;
            var sx = x;
            var dstOff = (y*w+x)*4;
            var r=0, g=0, b=0, a=0;
            for (var cy=0; cy<side; cy++) {
                for (var cx=0; cx<side; cx++) {
                    var scy = Math.min(sh-1, Math.max(0, sy + cy - halfSide));
                    var scx = Math.min(sw-1, Math.max(0, sx + cx - halfSide));
                    var srcOff = (scy*sw+scx)*4;
                    var wt = weights[cy*side+cx];
                    r += src[srcOff] * wt;
                    g += src[srcOff+1] * wt;
                    b += src[srcOff+2] * wt;
                    a += src[srcOff+3] * wt;
                }
            }
            dst[dstOff] = r;
            dst[dstOff+1] = g;
            dst[dstOff+2] = b;
            dst[dstOff+3] = a + alphaFac*(255-a);
        }
    }
    return output;
};

