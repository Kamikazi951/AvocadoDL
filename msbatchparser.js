var msBatchVideoParser = (function()
{
    function MsBatchVideoParser()
    {
    }

    MsBatchVideoParser.prototype = {

        parse: function (obj)
        {
            return msAbstractParser.parse(obj, [])
            .then(function(res)
            {
                if (res.hasOwnProperty("entries"))
                {
                    for (var i = res.entries.length - 1; i >= 0; --i)
                    {
                        if (!res.entries[i].hasOwnProperty("title"))
                            continue;
                        if (res.entries[i].title === "[Deleted video]" ||
                                res.entries[i].title === "[Private video]")
                        {
                            res.entries.splice(i, 1);
                        }
                    }
                }
                return res;
            });
        },

        isSupportedSource: msAbstractParser.isSupportedSource,

        supportedSourceCheckPriority: function()
        {
            return msAbstractParser.supportedSourceCheckPriority() + 1;
        },

        isPossiblySupportedSource: msAbstractParser.isPossiblySupportedSource,

        overrideUrlPolicy: msAbstractParser.overrideUrlPolicy,

        minIntevalBetweenQueryInfoDownloads: msAbstractParser.minIntevalBetweenQueryInfoDownloads
    };

    return new MsBatchVideoParser();
}());
