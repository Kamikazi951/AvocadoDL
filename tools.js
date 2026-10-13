function cookiesToNetscapeText(cookies)
{
	var r = "# Netscape HTTP Cookie File\n";

	for (var i = 0; i < cookies.length; ++i)
	{
		var c = cookies[i];

		var domain = String(c.domain || "");
		var expires = c.expirationDate;
		if (expires && typeof expires.getTime === "function") expires = expires.getTime() / 1000;
		else if (typeof expires === "string") expires = Date.parse(expires) / 1000;
		expires = isFinite(expires) && expires > 0 ? Math.floor(expires) : 0;
		var fields = [domain, domain.charAt(0) === '.' ? "TRUE" : "FALSE",
			 c.path || "/", (c.isSecure || c.secure) ? "TRUE" : "FALSE",
			 expires, c.name || "", c.value || ""];
		// Reject malformed entries rather than allowing extra Netscape rows.
		if (!domain || fields.some(function(value) { return /[\t\r\n]/.test(String(value)); })) continue;
		r += fields.join('\t');

		r += '\n';
	}

	return r;
}

function logPythonResult(obj)
{
   // Extractor output contains signed URLs and cookies. Do not log it.
   if (obj.errorOutput)
       console.log("AvocadoDL: extractor diagnostics available on failure.");
}

function logError(msg, detail)
{
   console.error("AvocadoDL:", msg, detail || "");
}
