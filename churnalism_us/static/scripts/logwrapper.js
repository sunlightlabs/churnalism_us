LogWrapper = function (loglevel) {
    if (this === undefined) {
        return new LogWrapper(loglevel);
    }
    var _this = this;

    var DEBUG = LogWrapper.DEBUG;
    var INFO = LogWrapper.INFO;
    var NOTICE = LogWrapper.NOTICE;
    var ERROR = LogWrapper.ERROR;
    var CRITICAL = LogWrapper.CRITICAL;

    var log = function (level, args) {
        // This line will trap errors in IE where console is not
        // defined until the console is opened.
        try {
            var _console = console; 
            var _log = _console.log;
        } catch (e) {
            return;
        }

        if ((loglevel !== undefined) && (level >= loglevel)) {
            if (console.log.apply !== undefined) {
                console.log.apply(console, args);
            } else {
                console.log(args.join(' '));
            }
        }
    };

    var debug = function (/* arguments */) {
        log(DEBUG, ['DEBUG:'].concat(Array.prototype.slice.call(arguments, 0)));
    };

    var info = function (/* arguments */) {
        log(INFO, ['INFO:'].concat(Array.prototype.slice.call(arguments, 0)));
    };

    var notice = function (/* arguments */) {
        log(NOTICE, ['NOTICE:'].concat(Array.prototype.slice.call(arguments, 0)));
    };

    var error = function (/* arguments */) {
        log(ERROR, ['ERROR:'].concat(Array.prototype.slice.call(arguments, 0)));
    };

    var critical = function (/* arguments */) {
        log(CRITICAL, ['CRITICAL:'].concat(Array.prototype.slice.call(arguments, 0)));
    };

    return {
        'loglevel': loglevel,
        'debug': debug,
        'info': info,
        'notice': notice,
        'error': error,
        'critical': critical
    };
};

LogWrapper.DEBUG = 10;
LogWrapper.INFO = 20;
LogWrapper.NOTICE = 30;
LogWrapper.ERROR = 40;
LogWrapper.CRITICAL = 50;

try {
    exports.EmitRR = EmitRR;
} catch (e) {
    /* Ignore -- we're in a content script */
}

