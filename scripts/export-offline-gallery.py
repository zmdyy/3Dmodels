#!/usr/bin/env python3
"""Build each catalog entry as a self-contained Chinese-named HTML page."""
import base64, html, json, mimetypes, os, re, subprocess, sys, urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_offline-output'/'3Dmodel2-中文离线案例'
BUNDLE=ROOT/'node_modules/.bin/esbuild'
SCRIPT=re.compile(r'<script\b([^>]*)>(.*?)</script\s*>',re.I|re.S)
LINK=re.compile(r'<link\b[^>]*>',re.I|re.S)
IMAGE=re.compile(r'<(?:img|source|video|audio)\b[^>]*>',re.I|re.S)
def attr(name,src):
 m=re.search(r'\b'+re.escape(name)+r'\s*=\s*(["\x27])(.*?)\1',src,re.I|re.S)
 return m.group(2) if m else None
URL_RE=re.compile(r'["\x27]([^"\x27\n\r]{1,220}\.(?:glb|gltf|bin|png|jpg|jpeg|webp|gif|svg|json|ktx2|hdr|exr|wasm|txt|mp3|ogg|wav|woff2?|ttf|otf)(?:\?[^"\x27\n\r]*)?)["\x27]',re.I)
CSS_URL=re.compile(r'url\(\s*(["\x27]?)([^)"\x27]+)\1\s*\)',re.I)
ASSET_EXT={'.glb','.gltf','.bin','.png','.jpg','.jpeg','.webp','.gif','.svg','.json','.ktx2','.hdr','.exr','.wasm','.txt','.mp3','.ogg','.wav','.woff','.woff2','.ttf','.otf'}
MIME={'.glb':'model/gltf-binary','.gltf':'model/gltf+json','.wasm':'application/wasm','.js':'application/javascript','.txt':'text/plain'}
def resolve(file,value):
 if not value or value.startswith(('data:','blob:','#','http:','https:','//','mailto:','javascript:')):return None
 url=urllib.parse.unquote(value.split('#')[0].split('?')[0]).strip()
 if not url:return None
 path=(file.parent/url).resolve()
 try:path.relative_to(ROOT)
 except ValueError:return None
 return path if path.is_file() else None
def uri(file):
 mime=MIME.get(file.suffix.lower()) or mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
 return 'data:'+mime+';base64,'+base64.b64encode(file.read_bytes()).decode('ascii')
def clean_name(title):
 name=re.sub(r'[\\/:*?"<>|\r\n]+',' · ',str(title))
 name=re.sub(r'\s+',' ',name).strip(' .')
 return (name[:85].rstrip(' .') or '未命名案例')+'.html'
def bundle_module(contents,source_path,html_path,imap,logs):
 if not BUNDLE.exists():
  logs.append('缺少 esbuild：'+source_path.name);return None
 aliases=[]
 imports=imap.get('imports',{}) if isinstance(imap,dict) else {}
 for key,val in imports.items():
  if not isinstance(val,str) or val.startswith(('http:','https:')):
   logs.append('外部 import map：'+key+' = '+str(val));continue
  abspath=(html_path.parent/val.split('?')[0]).resolve()
  if key.endswith('/'):aliases.append('--alias:'+key[:-1]+'='+str(abspath))
  elif abspath.exists():aliases.append('--alias:'+key+'='+str(abspath))
  else:logs.append('找不到 import map：'+val)
 contents=contents.replace('import.meta.url','document.baseURI')
 tmp=source_path.parent/('__offline_tmp_'+str(os.getpid())+'.js')
 try:
  tmp.write_text(contents,encoding='utf-8')
  r=subprocess.run([str(BUNDLE),str(tmp),'--bundle','--platform=browser','--format=iife','--target=es2020','--legal-comments=inline','--log-level=error',*aliases],capture_output=True,text=True,cwd=ROOT,timeout=90)
  if r.returncode:
   logs.append('模块构建失败 '+source_path.name+'：'+r.stderr[:350]);return None
  return r.stdout
 except Exception as e:
  logs.append('模块构建异常 '+source_path.name+'：'+str(e)[:220]);return None
 finally:tmp.unlink(missing_ok=True)
def runtime_patch(assets):
 data=json.dumps(assets,ensure_ascii=False,separators=(',',':')).replace('</script','<\\/script')
 return '<script>\n(function(){\nconst records='+data+''' ;
const nativeFetch=window.fetch.bind(window);
function lookup(raw){
 const str=String(raw instanceof Request?raw.url:raw);
 if(str.startsWith('data:')||str.startsWith('blob:'))return null;
 let path=str.split(/[?#]/)[0];
 try{path=decodeURIComponent(path);}catch(e){}
 path=path.replace(/\\\\/g,'/');
 const clean=path.replace(/^file:\\/\\/[^/]+/,'').replace(/^\\/+/, '');
 return records[clean]||records[path]||records[path.split('/').pop()]||null;
}
function bytes(x){const b=atob(x),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a;}
window.fetch=function(input,init){const found=lookup(input);if(found)return Promise.resolve(new Response(bytes(found[1]),{status:200,headers:{'Content-Type':found[0]}}));return nativeFetch(input,init);};
const oldOpen=XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open=function(method,url,...args){const f=lookup(url);if(f)return oldOpen.call(this,method,'data:'+f[0]+';base64,'+f[1],...args);return oldOpen.call(this,method,url,...args);};
const desc=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
if(desc&&desc.set){Object.defineProperty(HTMLImageElement.prototype,'src',{configurable:true,enumerable:desc.enumerable,get:desc.get,set(v){const f=lookup(v);return desc.set.call(this,f?'data:'+f[0]+';base64,'+f[1]:v);}});}
window.__OFFLINE_ASSET_COUNT=Object.keys(records).length;
})();
</script>'''
def make_index(rep):
 links=[]
 for it in rep['cases']:
  if 'file' not in it:continue
  name=html.escape(it['title']);path=urllib.parse.quote(it['file'])
  warn=' <small class="warn">待复核</small>' if it['warnings'] else ''
  links.append('<a href="'+path+'" target="_blank" rel="noopener">'+name+warn+'<span>↗</span></a>')
 return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>3Dmodel2 · 中文离线案例</title><style>body{margin:0;background:#f5f7f3;color:#20372f;font-family:"Microsoft YaHei",system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:55px 28px}h1{font-size:35px;margin-bottom:12px}.intro{color:#64766d;margin:0 0 35px}.search{width:100%;box-sizing:border-box;border:1px solid #cbd9d0;border-radius:12px;padding:15px;font-size:17px;background:white}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:13px;margin-top:26px}a{display:flex;gap:7px;align-items:center;justify-content:space-between;text-decoration:none;background:#fff;padding:18px 16px;border:1px solid #e1e7e1;border-radius:12px;color:#25483b;min-height:52px}a:hover{box-shadow:0 6px 20px #173b2530;border-color:#86ad96}a span{color:#729b8d;font-size:22px}.warn{font-size:11px;color:#99632b}small{margin-left:3px}footer{margin:40px 0;color:#718579;font-size:13px}</style></head><body><main><h1>3D 交互物理实验室</h1><p class="intro">共 '''+str(rep['exported_count'])+''' 个中文案例 · 双击任意 HTML 独立打开 · 附带导出检查报告。三维交互仍需逐机检查。</p><input class="search" id="q" placeholder="搜索实验名称…" oninput="document.querySelectorAll('.grid a').forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(this.value.toLowerCase()))"><div class="grid">'''+''.join(links)+'''</div><footer>报告：导出检查报告.json。无需联网或本地服务器。</footer></main></body></html>'''
def main():
 cd=(ROOT/'catalog.js').read_text(encoding='utf-8')
 match=re.search(r'window\.MODEL_CATALOG\s*=\s*(\[[\s\S]*?\])\s*;',cd)
 if not match:raise RuntimeError('无法读取 catalog.js')
 catalog=json.loads(match.group(1));OUT.mkdir(parents=True,exist_ok=True)
 report={'source':'zmdyy/3Dmodel2','catalog_count':len(catalog),'cases':[]}
 used=set()
 for i,entry in enumerate(catalog,1):
  origin=ROOT/entry['path'].split('?')[0];title=entry['title'];name=clean_name(title)
  if name in used:name=name[:-5]+'（'+str(i)+'）.html'
  used.add(name);logs=[]
  if not origin.exists():
   report['cases'].append({'title':title,'status':'失败','warnings':['源文件缺失 '+str(origin)]});continue
  page=origin.read_text(encoding='utf-8',errors='replace')
  if origin.name=='bicycle-v346.html':
   base=origin.parent/'bicycle-v346-assets'
   blocks=[base/('chunk-%02d.txt'%j) for j in range(24)]
   if all(p.exists() for p in blocks):
    page=''.join(p.read_text(encoding='utf-8',errors='replace') for p in blocks)
   else:logs.append('缺失自行车分包，不能独立运行')
  deferred=[];js_origins=[];imap={}
  for attrs,body in SCRIPT.findall(page):
   if (attr('type',attrs) or '').lower()=='importmap':
    try:imap.update(json.loads(body))
    except Exception:logs.append('无法解析 importmap')
  def script_sub(m):
   attrs,body=m.group(1),m.group(2)
   typ=(attr('type',attrs) or '').lower();src=attr('src',attrs)
   if typ=='importmap':return ''
   if typ in ('application/json','application/ld+json'):return m.group(0)
   if typ not in ('','module','text/javascript','application/javascript'):return m.group(0)
   f=resolve(origin,src) if src else None
   if src and not f:
    logs.append('外链脚本未内嵌：'+src);return m.group(0)
   if f:
    body=f.read_text(encoding='utf-8',errors='replace');js_origins.append((f,body))
   if typ=='module':
    compiled=bundle_module(body,f or origin,origin,imap,logs)
    if compiled is None:return m.group(0)
    deferred.append('<script>\n'+compiled.replace('</script','<\\/script')+'\n</script>')
    return ''
   tag='<script>\n'+body.replace('</script','<\\/script')+'\n</script>'
   if src and re.search(r'\bdefer\b',attrs,re.I):
    deferred.append(tag);return ''
   return tag if src else m.group(0)
  page=SCRIPT.sub(script_sub,page)
  def link_sub(m):
   tag=m.group(0);rel=(attr('rel',tag) or '').lower();href=attr('href',tag)
   if rel not in ('stylesheet','icon','shortcut icon','preload','modulepreload') or not href:return tag
   f=resolve(origin,href)
   if rel in ('preload','modulepreload'):return ''
   if not f:
    if rel=='stylesheet':logs.append('样式表缺失：'+href)
    return tag
   if rel in ('icon','shortcut icon'):
    return re.sub(r'\bhref\s*=\s*(["\x27]).*?\1','href="'+uri(f)+'"',tag,count=1,flags=re.I|re.S)
   css=f.read_text(encoding='utf-8',errors='replace')
   css=CSS_URL.sub(lambda u:'url("'+uri(g)+'")' if (g:=resolve(f,u.group(2))) else u.group(0),css)
   return '<style>\n'+css.replace('</style','<\\/style')+'\n</style>'
  page=LINK.sub(link_sub,page)
  def img_sub(m):
   tag=m.group(0);src=attr('src',tag);f=resolve(origin,src) if src else None
   if not f:return tag
   return re.sub(r'\bsrc\s*=\s*(["\x27]).*?\1','src="'+uri(f)+'"',tag,count=1,flags=re.I|re.S)
  page=IMAGE.sub(img_sub,page)
  paths=set()
  for base,source in [(origin,page),*js_origins]:
   for ref in URL_RE.findall(source):
    f=resolve(base,ref)
    if f and f.suffix.lower() in ASSET_EXT:paths.add(f)
  folder=origin.with_name(origin.stem+'-assets')
  if folder.is_dir() and origin.name!='bicycle-v346.html':
   paths.update(p for p in folder.rglob('*') if p.is_file())
  for p in origin.parent.glob(origin.stem.split('-')[0]+'*.glb'):
   if p.is_file():paths.add(p)
  packed={}
  for f in sorted(paths):
   mime=MIME.get(f.suffix.lower()) or mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
   v=[mime,base64.b64encode(f.read_bytes()).decode('ascii')]
   packed.setdefault(f.name,v)
   packed.setdefault(f.relative_to(ROOT).as_posix(),v)
   packed.setdefault(f.as_posix().split('/models/',1)[-1],v)
  page=re.sub(r'<head\b[^>]*>',lambda m:m.group(0)+'\n'+runtime_patch(packed),page,count=1,flags=re.I)
  if deferred:page=re.sub(r'</body\s*>',lambda m:'\n'+'\n'.join(deferred)+'\n</body>',page,count=1,flags=re.I)
  target=OUT/name;target.write_text(page,encoding='utf-8')
  status='待复核' if logs else '已导出（静态检查）'
  info={'title':title,'file':name,'size':target.stat().st_size,'assets_embedded':len(paths),'status':status,'warnings':logs}
  report['cases'].append(info)
  print('%3d/%d %-8s %9d %s'%(i,len(catalog),status,info['size'],title),flush=True)
 report['exported_count']=len([x for x in report['cases'] if 'file' in x])
 report['warning_count']=len([x for x in report['cases'] if x['warnings']])
 (OUT/'导出检查报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'index.html').write_text(make_index(report),encoding='utf-8')
 print('EXPORTED',report['exported_count'],'/',len(catalog),'WARNINGS',report['warning_count'])
 return 0 if report['exported_count']==len(catalog) else 2
if __name__=='__main__':sys.exit(main())
