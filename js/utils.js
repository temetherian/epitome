var utils = (function() {
    var utils = Object();
    utils.is_null_or_undefined = function(thing) {
        return _.isNull(thing) || _.isUndefined(thing);
    }
    ;
    return utils;
}());
