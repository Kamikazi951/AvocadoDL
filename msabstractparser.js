var g_configPromise = null;
var g_configLoadedAt = 0;
var g_config = null;

var YTDLP_SCRIPT = "ytdlp_runner.py";

var msAbstractParser = (function()
{
    function MsAbstractParser()
    {
    }

    function loadConfig(requestId, interactive)
    {
        if (g_configPromise && Date.now() - g_configLoadedAt < 60000)
            return g_configPromise;
        g_configLoadedAt = Date.now();

        g_configPromise = launchPythonScript(requestId, interactive, "config_loader.py", [])
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
            console.log("AvocadoDL: configuration unavailable; using defaults.");
        });
        return g_configPromise;
    }

    function buildArgs(customArgs)
    {
        var args = [];

        args.push("--ignore-config", "--no-plugin-dirs", "-J", "--flat-playlist", "--skip-download", "--socket-timeout", "20", "--retries", "2", "--extractor-retries", "2", "--compat-options", "no-youtube-unavailable-videos");

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

        if (g_config && Array.isArray(g_config.extra_ytdlp_args))
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
            if (!obj || !/^https?:\/\//i.test(obj.url || ""))
                return Promise.reject({error: "Only HTTP and HTTPS URLs can be parsed.", isParseError: true});
            console.log("AvocadoDL: parsing media");

            var tmpCookies;

            return loadConfig(obj.requestId, obj.interactive)
            .then(function()
            {
                var args = buildArgs(customArgs);

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

                var proxyUrl = "";
                try { proxyUrl = qtJsNetworkProxyMgr.proxyForUrl(obj.url).url(); } catch (e) {}
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
                        if (typeof browser === "string" && /^(chrome|chromium|firefox|brave|edge|opera|vivaldi|safari)(:|$)/i.test(browser))
                            args.push('--cookies-from-browser', browser);

                    }
                }

                var userAgent = obj.userAgent || systemUserAgent;
                if (userAgent)
                    args.push('--user-agent', userAgent);

                if (obj.referrer || obj.referer)
                    args.push('--referer', obj.referrer || obj.referer);
                // The parser only queries metadata; user flags cannot turn it into a download.
                args.push('--dump-single-json', '--skip-download', '--', obj.url);

                return launchPythonScript(obj.requestId, obj.interactive, YTDLP_SCRIPT, args);
            })
            .then(function(obj)
            {
                logPythonResult(obj);

                return new Promise(function (resolve, reject)
                {
                    var output = (obj.output || "").trim();
                    if (!output || output[0] !== '{')
                    {
                        var errOutput = obj.errorOutput || "";
                        var errorMsg = "Parse error";

                        if (/ERROR:\s*(\[generic\])?\s*Unsupported URL:/.test(errOutput))
                            errorMsg = "Unsupported URL";
                        else if (/ERROR:.*HTTP Error 403/.test(errOutput))
                            errorMsg = "Access denied (403). Try setting cookies_browser in settings.";
                        else if (/ERROR:.*Private video/.test(errOutput))
                            errorMsg = "Private video.";
                        else if (/ERROR:.*Video unavailable/.test(errOutput))
                            errorMsg = "Video unavailable.";
                        else if (/Sign in to confirm/.test(errOutput))
                            errorMsg = "Age-restricted. Use cookies_browser in settings.";
                        else if (/DRM/i.test(errOutput))
                            errorMsg = "This video is DRM protected and cannot be downloaded.";
                        else if (/cookies|decrypt|database/i.test(errOutput))
                            errorMsg = "Browser cookies are unavailable. Use a Netscape cookies file in extra_ytdlp_args for sign-in-only videos.";
                        else if (errOutput)
                            errorMsg = (errOutput.match(/^ERROR:.*$/m) || [errOutput.split("\n")[0]])[0];

                        reject({
                                   error: errorMsg,
                                   isParseError: true
                               });
                    }
                    else
                    {
                        try { resolve(JSON.parse(output)); }
                        catch (e) { reject({error: "The extractor returned invalid JSON. Update the add-on and retry.", isParseError: true}); }
                    }
                });
            }).then(function(result) {
                tmpCookies = null;
                return result;
            }, function(error) {
                tmpCookies = null;
                throw error;
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
            if (obj.contentType && !/^(text\/html|application\/xhtml\+xml|application\/(x-mpegurl|vnd\.apple\.mpegurl|dash\+xml)|audio\/(x-mpegurl|mpegurl))(;.*)?$/i.test(obj.contentType))
                return false;
            if (obj.resourceSize !== -1 &&
                    (obj.resourceSize === 0 || obj.resourceSize > 20*1024*1024))
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
        }


    };

    return new MsAbstractParser();
}());
