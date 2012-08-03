(function(){
    /* Generates name based UUIDs (versions 3 and 5).
     * Requires CryptoJS for the hash functions.
     * RFC4122 is horrible: http://www.ietf.org/rfc/rfc4122.txt
     * This document was tremendously helpful: http://www.famkruithof.net/guid-uuid-namebased.html
     */

    UUID = function (words) {
        this._words = words;
    };

    UUID.NAMESPACE_DNS = [107, 167, 184, 16, 157, 173, 17, 209, 128, 180, 0, 192, 79, 212, 48, 200];
    UUID.NAMESPACE_URL = [107, 167, 184, 17, 157, 173, 17, 209, 128, 180, 0, 192, 79, 212, 48, 200];

    UUID.prototype.toString = function (fmt) {
        var str = this._words.toString().substr(0, 32);
        if (fmt == '-') {
            return [str.substr(0, 8), str.substr(8, 4), str.substr(12, 4), str.substr(16, 4), str.substr(20, 12)].join('-');
        } else {
            return str;
        }
    };

    UUID.uuid3 = function (ns, name) {
        var words = as_word_array(ns);
        words.concat(CryptoJS.enc.Utf8.parse(name))
        var hash_words = CryptoJS.MD5(words);
        _set_uuid_version(hash_words, 3);
        return new UUID(hash_words);
    };

    UUID.uuid5 = function (ns, name) {
        var words = as_word_array(ns);
        words.concat(CryptoJS.enc.Utf8.parse(name))
        var hash_words = CryptoJS.SHA1(words);
        _set_uuid_version(hash_words, 5);
        return new UUID(hash_words);
    };

    UUID.inject = function (NS) {
        NS.UUID = UUID;
        NS.NAMESPACE_DNS = UUID.NAMESPACE_DNS;
        NS.NAMESPACE_URL = UUID.NAMESPACE_URL;
        NS.uuid3 = UUID.uuid3;
        NS.uuid5 = UUID.uuid5;
    };

    var chunked = function (lst, sz) {
        var newlst = [];
        var chunk = [];
        var ix = 0;
        while (ix < lst.length) {
            chunk.push(lst[ix]);
            if (chunk.length == sz) {
                newlst.push(chunk);
                chunk = [];
            }
            ix += 1;
        }
        if (chunk.length > 0) {
            newlst.push(chunk);
        }
        return newlst;
    };

    var as_word_array = function (bytes) {
        var ws = [];
        var chunks = chunked(bytes, 4);
        for (var ix = 0; ix < chunks.length; ix++) {
            var chunk = chunks[ix];
            var n = 0;
            for (var jx = 0; jx < chunk.length; jx++) {
                n |= (chunk[jx] << (8 * (3-jx)));
            }
            ws.push(n);
        }
        return CryptoJS.lib.WordArray.create(ws);
    };

    var _set_uuid_version = function (hash_words, version) {
        var byte7 = ((hash_words.words[1] & 0x0000ff00) >> 8);
        byte7 &= 0x0f;
        byte7 |= ((version == 3) ? 0x30 : 0x50);
        hash_words.words[1] &= 0xffff00ff;
        hash_words.words[1] |= (byte7 << 8);
        var byte9 = ((hash_words.words[2] & 0xff000000) >> 24);
        byte9 &= 0x3f;
        byte9 |= 0x80;
        hash_words.words[2] &= 0x00ffffff;
        hash_words.words[2] |= (byte9 << 24);
    };
})();
