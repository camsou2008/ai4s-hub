#!/usr/bin/env python3
"""Rebuild ~/workspace/publish/ai4s/api-data.js from the JSON datasets in
~/workspace/publish/ai4s_api_backup/. Run after any dataset change."""
import json, glob, os

HOME = os.path.expanduser('~')
BACKUP = os.path.join(HOME, 'workspace/publish/ai4s_api_backup')
PUBLISH = os.path.join(HOME, 'workspace/publish/ai4s')

facets = json.load(open(f'{BACKUP}/facets.json'))
overview = json.load(open(f'{BACKUP}/overview.json'))
signals = json.load(open(f'{BACKUP}/signals.json'))['items']
cases = json.load(open(f'{BACKUP}/cases.json'))['items']
articles = []
for k in ['report', 'daily', 'weekly']:
    p = f'{BACKUP}/articles_{k}.json'
    if os.path.exists(p):
        articles += json.load(open(p))['items']
details = {}
for f in glob.glob(f'{BACKUP}/article_details/*.json'):
    d = json.load(open(f))
    details[d['slug']] = d
    details[str(d['id'])] = d

db = {'facets': facets, 'overview': overview, 'signals': signals,
      'cases': cases, 'articles': articles, 'articleDetails': details}
db_js = json.dumps(db, ensure_ascii=False, separators=(',', ':')).replace('</script', '<\\/script')

patch = r'''
;(function(){
  var DB = window.__AI4S_API__ || {};
  function matchQ(item,q,fields){
    q=(q||'').trim().toLowerCase(); if(!q) return true;
    for(var i=0;i<fields.length;i++){var v=item[fields[i]];
      if(v && String(v).toLowerCase().indexOf(q)!==-1) return true;}
    return false;
  }
  function paginate(arr,limit,offset){
    offset=offset||0;
    if(limit==null||isNaN(limit)) return arr.slice(offset);
    return arr.slice(offset,offset+limit);
  }
  function toInt(v,def){ v=parseInt(v==null?'':v,10); return isNaN(v)?def:v; }
  function handleSignals(sp){
    var items=(DB.signals||[]).slice();
    var days=toInt(sp.get('days'),0);
    if(days>0){
      var mx=''; for(var i=0;i<items.length;i++){var d=items[i].occurred_on||''; if(d>mx)mx=d;}
      if(mx){var cut=new Date(mx+'T00:00:00Z'); cut.setUTCDate(cut.getUTCDate()-(days-1));
        var cutS=cut.toISOString().slice(0,10);
        items=items.filter(function(s){return (s.occurred_on||'')>=cutS;});}
    }
    var layer=sp.get('layer');
    if(layer&&layer!=='\u5168\u90e8') items=items.filter(function(s){return s.layer===layer;});
    var q=sp.get('q')||'';
    items=items.filter(function(s){return matchQ(s,q,['org','summary','source_title','region']);});
    return {items:paginate(items,toInt(sp.get('limit'),60),toInt(sp.get('offset'),0))};
  }
  function handleCases(sp){
    var items=(DB.cases||[]).slice();
    var country=sp.get('country');
    if(country&&country!=='\u5168\u90e8') items=items.filter(function(c){return c.country===country;});
    var layer=sp.get('layer');
    if(layer&&layer!=='\u5168\u90e8') items=items.filter(function(c){return c.layer===layer;});
    var q=sp.get('q')||'';
    items=items.filter(function(c){return matchQ(c,q,['org','org_en','platform','highlights','country','source_title']);});
    return {items:paginate(items,toInt(sp.get('limit'),200),toInt(sp.get('offset'),0))};
  }
  function handleArticles(sp){
    var items=(DB.articles||[]).slice();
    var kind=sp.get('kind');
    if(kind) items=items.filter(function(a){return a.kind===kind;});
    var q=sp.get('q')||'';
    items=items.filter(function(a){return matchQ(a,q,['title','dek']);});
    items=paginate(items,sp.has('limit')?toInt(sp.get('limit'),null):null,toInt(sp.get('offset'),0));
    if(sp.get('body')==='1') items=items.map(function(a){return DB.articleDetails[a.slug]||DB.articleDetails[String(a.id)]||a;});
    return {items:items};
  }
  function route(path,sp){
    if(path==='/api/facets') return {status:200,body:DB.facets};
    if(path==='/api/overview') return {status:200,body:DB.overview};
    if(path==='/api/signals') return {status:200,body:handleSignals(sp)};
    if(path==='/api/cases') return {status:200,body:handleCases(sp)};
    if(path==='/api/articles') return {status:200,body:handleArticles(sp)};
    var m=path.match(/^\/api\/articles\/(.+)$/);
    if(m){var d=DB.articleDetails[decodeURIComponent(m[1])];
      if(d) return {status:200,body:d};
      return {status:404,body:{error:'not found'}};}
    return null;
  }
  var origFetch=window.fetch.bind(window);
  window.fetch=function(input,init){
    var urlStr=(typeof input==='string')?input:(input&&input.url);
    try{
      var u=new URL(urlStr,window.location.href);
      if(u.origin===window.location.origin&&u.pathname.indexOf('/api/')===0){
        var r=route(u.pathname,u.searchParams);
        if(r) return Promise.resolve(new Response(JSON.stringify(r.body),
          {status:r.status,headers:{'content-type':'application/json'}}));
      }
    }catch(e){}
    return origFetch(input,init);
  };
})();
'''

out = 'window.__AI4S_API__=' + db_js + ';' + patch
dest = os.path.join(PUBLISH, 'api-data.js')
open(dest, 'w').write(out)
print('wrote %s (%.0f KB): %d signals, %d cases, %d articles' % (
    dest, len(out) / 1024, len(signals), len(cases), len(articles)))
