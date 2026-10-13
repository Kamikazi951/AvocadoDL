const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
function setup(result = {output:'{"id":"fixture"}'}, config = {}) {
  const calls = [];
  const context = vm.createContext({console, Promise, Date,
    launchPythonScript: async (id, interactive, script, args) => {
      calls.push({script,args});
      return script === 'config_loader.py' ? {output:JSON.stringify(config)} : result;
    }
  });
  for (const file of ['tools.js','msabstractparser.js','msparser.js','msbatchparser.js']) {
    vm.runInContext(fs.readFileSync(path.join(__dirname,'..',file),'utf8'), context);
  }
  return {context,calls};
}
test('cookies preserve domains, paths, session cookies and seconds/date expiry', () => {
  const {context} = setup();
  const text = context.cookiesToNetscapeText([
    {domain:'.example.org',path:'/video',isSecure:true,expirationDate:2000000000,name:'a',value:'1'},
    {domain:'example.org',expirationDate:new Date(2000000000000),name:'b',value:'2'},
    {domain:'example.org',name:'session',value:'3'},
    {domain:'example.org',name:'injected\nrow',value:'4'}
  ]);
  assert(text.includes('.example.org\tTRUE\t/video\tTRUE\t2000000000'));
  assert(text.includes('example.org\tFALSE\t/\tFALSE\t0\tsession\t3'));
  assert(!text.includes('injected'));
});
test('concurrent parses share initialization and pass referer, URL separator and metadata flags', async () => {
  const {context,calls} = setup();
  await Promise.all([1,2].map(requestId => context.msParser.parse({requestId,url:'https://example.org/v',referrer:'https://example.org/'})));
  assert.equal(calls.filter(call=>call.script==='config_loader.py').length,1);
  const args=calls.find(call=>call.script==='ytdlp_runner.py').args;
  assert(args.includes('--referer'));
  assert(args.includes('--ignore-config'));
  assert(args.includes('--skip-download'));
  assert.deepEqual(Array.from(args.slice(-2)),['--','https://example.org/v']);
});
test('malformed extractor JSON produces a user-facing parse error', async () => {
  const {context} = setup({output:'{invalid'});
  await assert.rejects(context.msParser.parse({url:'https://example.org'}), error=>error.isParseError && /invalid JSON/.test(error.error));
});
test('missing proxy APIs and browser cookies do not break public parsing', async () => {
  const {context,calls}=setup({output:'{"id":"ok"}'},{cookies_browser:'chrome'});
  await context.msParser.parse({url:'https://example.org'});
  assert(calls.some(call=>call.args.includes('--cookies-from-browser')));
});
test('null/deleted/private playlist entries are removed', async () => {
  const {context}=setup({output:JSON.stringify({entries:[null,{title:'[Deleted video]'},{title:'[Private video]'},{id:'valid'}]})});
  const result=await context.msBatchVideoParser.parse({url:'https://example.org'});
  assert.equal(result.entries.length,1);
  assert.equal(result.entries[0].id,'valid');
});
test('stream manifests and XHTML are accepted for parsing', () => {
  const {context}=setup();
  for (const contentType of ['application/vnd.apple.mpegurl','application/dash+xml','application/xhtml+xml','Text/HTML; charset=UTF-8']) {
    assert(context.msParser.isPossiblySupportedSource({url:'https://example.org',contentType,resourceSize:-1}));
  }
});
