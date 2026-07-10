var g_browsers = Object.create(null);
var g_config = null;

var YTDLP_SCRIPT = "yt-dlp/yt_dlp/__main__.py";

var msAbstractParser = (function()
{
    function MsAbstractParser()
    {
    }

    function loadConfig(requestId, interactive)
    {
        if (g_config)
            return Promise.resolve();

        return launchPythonScript(requestId, interactive, "config_loader.py", [])
        .then(function(obj)
        {
            var out = obj.output.trim();
            if (out && out[0] === '{')
            {
                g_config = JSON.parse(out);
                console.log("AvocadoDL: config loaded");
            }
            else
            {
                g_config = {};
            }
        })
        .then(function()
        {
            if (!g_config.auto_update_ytdlp)
                return;

            return launchPythonScript(requestId, interactive, "ytdlp_helper.py", [])
            .then(function(obj)
            {
                logPythonResult(obj);
            });
        })
        .catch(function(e)
        {
            if (!g_config)
                g_config = {};
            console.log("AvocadoDL: init warning:", e.error || e);
        });
    }

    function buildArgs(customArgs)
    {
        var args = [];

        args.push("-J", "--flat-playlist", "--no-warnings", "--compat-options", "no-youtube-unavailable-videos");

        if (g_config && g_config.format)
            args.push("-f", g_config.format);

        if (g_config && g_config.output_template)
            args.push("-o", g_config.output_template);

        if (g_config && g_config.embed_thumbnail)
            args.push("--embed-thumbnail");

        if (g_config && g_config.extract_audio)
        {
            args.push("-x");
            if (g_config.audio_format)
                args.push("--audio-format", g_config.audio_format);
            if (g_config.audio_quality)
                args.push("--audio-quality", g_config.audio_quality);
        }

        if (g_config && g_config.write_subs)
        {
            args.push("--write-subs", "--write-auto-subs");
            if (g_config.sub_langs)
                args.push("--sub-langs", g_config.sub_langs);
        }

        if (g_config && g_config.download_archive)
            args.push("--download-archive", g_config.download_archive);

        if (g_config && g_config.limit_rate)
            args.push("-r", g_config.limit_rate);

        if (g_config && g_config.extra_ytdlp_args)
        {
            for (var i = 0; i < g_config.extra_ytdlp_args.length; ++i)
                args.push(g_config.extra_ytdlp_args[i]);
        }

        if (customArgs && customArgs.length)
            args = args.concat(customArgs);

        return args;
    }

    MsAbstractParser.prototype = {

        parse: function (obj, customArgs)
        {
            console.log("AvocadoDL: parsing", obj.url);

            var self = this;

            return loadConfig(obj.requestId, obj.interactive)
            .then(function()
            {
                var args = buildArgs(customArgs);
                var tmpCookies;
                var systemUserAgent;
                var systemBrowser;
                var allowWbCookies = true;

                try
                {
                    systemUserAgent = qtJsSystem.defaultUserAgent;
                    systemBrowser = qtJsSystem.defaultWebBrowser;
                    allowWbCookies = App.pluginsAllowWbCookies;
                }
                catch(e) {}

                var proxyUrl = qtJsNetworkProxyMgr.proxyForUrl(obj.url).url();
                if (proxyUrl)
                {
                    proxyUrl = proxyUrl.replace(/^https:\/\//i, 'http://');
                    args.push("--proxy", proxyUrl);
                }
                else if (g_config && g_config.proxy)
                {
                    args.push("--proxy", g_config.proxy);
                }

                if (allowWbCookies)
                {
                    if (obj.cookies && obj.cookies.length)
                    {
                        tmpCookies = qtJsTools.createTmpFile("request_" + obj.requestId + "_cookies");
                        if (tmpCookies && tmpCookies.writeText(cookiesToNetscapeText(obj.cookies)))
                            args.push("--cookies", tmpCookies.path);
                    }
                    else
                    {
                        var browser = (g_config && g_config.cookies_browser) || obj.browser || systemBrowser;
                        if (browser)
                        {
                            if (!(browser in g_browsers))
                            {
                                return self.checkBrowser(obj.requestId, obj.interactive, browser)
                                    .then(function() { return self.parse(obj, customArgs); });
                            }

                            if (!g_browsers[browser] && browser !== "firefox")
                            {
                                browser = "firefox";
                                if (!(browser in g_browsers))
                                {
                                    return self.checkBrowser(obj.requestId, obj.interactive, browser)
                                        .then(function() { return self.parse(obj, customArgs); });
                                }
                            }

                            if (g_browsers[browser])
                                args.push('--cookies-from-browser', browser);
                        }
                    }
                }

                var userAgent = obj.userAgent || systemUserAgent;
                if (userAgent)
                    args.push('--user-agent', userAgent);

                args.push(obj.url);

                return launchPythonScript(obj.requestId, obj.interactive, YTDLP_SCRIPT, args);
            })
            .then(function(obj)
            {
                logPythonResult(obj);

                return new Promise(function (resolve, reject)
                {
                    var output = obj.output.trim();
                    if (!output || output[0] !== '{')
                    {
                        var errOutput = obj.errorOutput || "";
                        var errorMsg = "Parse error";

                        if (/ERROR:\s*(\[generic\])?\s*Unsupported URL:/.test(errOutput))
                            errorMsg = "Unsupported URL";
                        else if (/ERROR:.*HTTP Error 403/.test(errOutput))
                            errorMsg = "Access denied (403). Try setting cookies_from_browser in settings.";
                        else if (/ERROR:.*Private video/.test(errOutput))
                            errorMsg = "Private video.";
                        else if (/ERROR:.*Video unavailable/.test(errOutput))
                            errorMsg = "Video unavailable.";
                        else if (/Sign in to confirm/.test(errOutput))
                            errorMsg = "Age-restricted. Use cookies_from_browser in settings.";
                        else if (errOutput)
                            errorMsg = errOutput.replace(/^ERROR:\s*/, "").split("\n")[0];

                        reject({
                                   error: errorMsg,
                                   isParseError: true
                               });
                    }
                    else
                    {
                        resolve(JSON.parse(output));
                    }
                });
            });
        },

        isSupportedSource: function(url)
        {
            return false;
        },

        supportedSourceCheckPriority: function()
        {
            return 0;
        },

        isPossiblySupportedSource: function(obj)
        {
            if (obj.contentType && !/^text\/html(;.*)?$/.test(obj.contentType))
                return false;
            if (obj.resourceSize !== -1 &&
                    (obj.resourceSize === 0 || obj.resourceSize > 3*1024*1024))
            {
                return false;
            }
            return /^https?:\/\//.test(obj.url);
        },

        overrideUrlPolicy: function(url)
        {
            return true;
        },

        minIntevalBetweenQueryInfoDownloads: function()
        {
            return 300;
        },

        checkBrowser: function(requestId, interactive, browser)
        {
            console.log("AvocadoDL: checking browser support (", browser, ")...");

            return launchPythonScript(requestId, interactive, YTDLP_SCRIPT, ['--cookies-from-browser', browser, 'e692ec362191442c960a761ac6b84878://test.test'])
            .then(function(obj)
            {
                logPythonResult(obj);

                return new Promise(function (resolve, reject)
                {
                    var isSupported = /"e692ec362191442c960a761ac6b84878"/.test(obj.errorOutput);
                    console.log("AvocadoDL:", browser, "supported:", isSupported);
                    g_browsers[browser] = isSupported;
                    resolve();
                });
            });
        }
    };

    return new MsAbstractParser();
}());
