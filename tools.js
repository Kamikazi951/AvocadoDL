function cookiesToNetscapeText(cookies)
{
	var r = "# Netscape HTTP Cookie File\n";

	for (var i = 0; i < cookies.length; ++i)
	{
		var c = cookies[i];

		r += c.domain + '\t' +
			 "FALSE" + '\t' +
			 "/" + '\t' +
			 (c.isSecure ? "TRUE" : "FALSE") + '\t' +
			 (Math.floor(c.expirationDate.getTime() / 1000) || 0) + '\t' +
			 c.name + '\t' +
			 c.value;

		r += '\n';
	}

	return r;
}

function logPythonResult(obj)
{
   if (obj.output)
       console.log("Python result: ", obj.output);

   if (obj.errorOutput)
       console.log("Python errors: ", obj.errorOutput);
}

function logError(msg, detail)
{
   console.error("AvocadoDL:", msg, detail || "");
}
