#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ai-books 下一本书的目录（如 e2b-infra/、firecracker/）打成一个自包含的单文件 HTML。

用法: python3 build_docs_html.py <书目录> <mermaid.min.js> <输出 html>
书名取自 <书目录>/README.md 的一级标题。

产物特点：双击即看，无需任何工具；mermaid 内联渲染；三张 SVG 嵌进附录；
所有跨文档链接与锚点改写成页内跳转，因此永远不会断。
"""
import html
import os
import re
import sys
from urllib.parse import unquote

from markdown_it import MarkdownIt

DOCS_DIR, MERMAID_JS, OUT = sys.argv[1:4]


# 书名：唯一来源是 <书目录>/README.md 顶部的一级标题
_readme_head = open(os.path.join(DOCS_DIR, 'README.md'), encoding='utf-8').read(2000)
_t = re.search(r'^#\s+(.+?)\s*$', _readme_head, re.M)
if not _t:
    sys.exit('README.md 顶部缺少一级标题（书名）')
BOOK_TITLE = _t.group(1)


def slug(t):
    """与 GitHub 一致的标题锚点规则（中文原样保留）。"""
    t = t.strip().lower()
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'`([^`]*)`', r'\1', t)
    t = re.sub(r'\*\*?([^*]*)\*\*?', r'\1', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'[^\w一-鿿\- ]', '', t)
    return t.replace(' ', '-')


def collect():
    files = sorted(os.listdir(DOCS_DIR))
    numbered = [f for f in files if re.match(r'^\d\d-.*\.md$', f)]
    out = []
    if 'README.md' in files:
        out.append('README.md')
    out += numbered
    for extra in ('STYLE.md', 'FIGURE-GUIDE.md', 'OUTLINE.md'):
        if extra in files:
            out.append(extra)
    return out


def doc_id(fn):
    return 'doc--' + fn[:-3]


def title_of(fn, src):
    m = re.search(r'^#\s+(.*)$', src, re.M)
    return re.sub(r'`', '', m.group(1)) if m else fn


def slug_frag(f):
    """md 里手写的锚点已经是 slug 形式，原样用；顺带兜住偶发的大小写差异。"""
    return f.lower()


md = MarkdownIt('commonmark').enable(['table', 'strikethrough'])

files = collect()
known = {f for f in files}

# ── 部分结构：从 README.md 的「### 第X部分」与其下表格里的文件名得到 文件 → 部分 ──
part_of, parts = {}, []
readme = open(os.path.join(DOCS_DIR, 'README.md'), encoding='utf-8').read() if 'README.md' in files else ''
cur = None
for line in readme.splitlines():
    m = re.match(r'^###\s+(.*)$', line)
    if m:
        cur = re.sub(r'\s+', ' ', m.group(1).replace('\u3000', ' ')).strip()
        parts.append(cur)
        continue
    for fnm in re.findall(r'\((\d\d-[^)]+\.md)\)', line):
        if cur and fnm not in part_of:
            part_of[fnm] = cur

sections, toc = [], []

for fn in files:
    src = open(os.path.join(DOCS_DIR, fn), encoding='utf-8').read()
    did = doc_id(fn)
    tokens = md.parse(src)

    heads = []

    def fix_link(tk):
        """链接改写：一切都变成页内锚点，解包后不可能断。"""
        href = unquote(tk.attrGet('href') or '')
        if href.startswith(('http://', 'https://', 'mailto:')):
            tk.attrSet('target', '_blank')
            tk.attrSet('rel', 'noopener')
            return
        if href.startswith('#'):
            tk.attrSet('href', f'#{did}--{slug_frag(href[1:])}')
            return
        if href.startswith('../'):
            tk.attrSet('title', '外部文件：' + href + '（需在完整仓库中打开）')
            return
        m = re.match(r'^([^#]+\.md)(?:#(.*))?$', href)
        if m and os.path.basename(m.group(1)) in known:
            tgt = doc_id(os.path.basename(m.group(1)))
            tk.attrSet('href', f'#{tgt}--{slug_frag(m.group(2))}' if m.group(2) else f'#{tgt}')
        elif m:
            tk.attrSet('title', '编写用文件：' + href + '（未收录进打包件，需在仓库中打开）')
            tk.attrSet('class', 'ext')

    def walk(tks):
        """inline 内容的 link_open 在 children 里，必须递归。"""
        for tk in tks:
            if tk.type == 'link_open':
                fix_link(tk)
            if tk.children:
                walk(tk.children)

    for i, tk in enumerate(tokens):
        # 标题：加上「文档前缀 + GitHub 规则锚点」的 id，并记进目录
        if tk.type == 'heading_open':
            text = tokens[i + 1].content
            anchor = f'{did}--{slug(text)}'
            tk.attrSet('id', anchor)
            lvl = int(tk.tag[1])
            if lvl == 1:
                tk.attrSet('class', 'doc-title')
            if lvl in (2, 3):
                heads.append((lvl, re.sub(r'[`*]', '', text), anchor))

    walk(tokens)

    body = md.renderer.render(tokens, md.options, {})
    # mermaid 代码块 → figure + 图号（图 NN-k；非正文文件只编号不带篇号）
    chap = fn[:2] if re.match(r'^\d\d-', fn) else None
    fig_n = [0]

    def fig(m):
        fig_n[0] += 1
        label = f'图 {int(chap)}-{fig_n[0]}' if chap else f'图 {fig_n[0]}'
        return (f'<figure class="fig"><div class="mermaid">{m.group(1)}</div>'
                f'<figcaption>{label}</figcaption></figure>')
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', fig, body, flags=re.S)
    # 篇首题注（h1 后紧跟的引用块）→ 卡片
    body = re.sub(r'(</h1>\s*)<blockquote>', r'\1<blockquote class="lede">', body, count=1)

    sections.append([did, fn, body])
    toc.append((did, title_of(fn, src), heads))

# 眉题与上一篇 / 下一篇
numbered = [(i, sec) for i, sec in enumerate(sections) if re.match(r'^\d\d-', sec[1])]
for k, (i, sec) in enumerate(numbered):
    did, fn, body = sec
    part = part_of.get(fn, '')
    eyebrow = f'<div class="eyebrow">{html.escape(part)}{" · " if part else ""}第 {int(fn[:2])} 篇</div>'
    nav_links = []
    if k > 0:
        pd, pf, _ = numbered[k - 1][1]
        nav_links.append(f'<a class="prev" href="#{pd}">← {html.escape(toc[numbered[k-1][0]][1])}</a>')
    if k + 1 < len(numbered):
        nd, nf, _ = numbered[k + 1][1]
        nav_links.append(f'<a class="next" href="#{nd}">{html.escape(toc[numbered[k+1][0]][1])} →</a>')
    sec[2] = eyebrow + body + '<nav class="pn">' + ''.join(nav_links) + '</nav>'
sections = [f'<section class="doc" id="{did}">\n{body}\n</section>' for did, fn, body in sections]

# ── 目录 ──
nav = []
open_part = None
def nav_entry(did, t, heads):
    out = [f'<li class="nav-doc"><a href="#{did}">{html.escape(t)}</a>']
    subs = [(text, anchor) for lvl, text, anchor in heads if lvl == 2]
    if subs:
        out.append('<ul class="nav-sub">' + ''.join(f'<li><a href="#{a}">{html.escape(x)}</a></li>' for x, a in subs) + '</ul>')
    out.append('</li>')
    return ''.join(out)
for (did, t, heads), fn in zip(toc, files):
    part = part_of.get(fn) if re.match(r'^\d\d-', fn) else None
    if part != open_part:
        if open_part is not None:
            nav.append('</ul></li>')
        if part is not None:
            nav.append(f'<li class="nav-part"><button type="button">{html.escape(part)}</button><ul>')
        open_part = part
    nav.append(nav_entry(did, t, heads))
if open_part is not None:
    nav.append('</ul></li>')

mermaid_src = open(MERMAID_JS, encoding='utf-8').read()
TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
mermaid_cfg = open(os.path.join(TOOLS_DIR, 'mermaid-config.json'), encoding='utf-8').read()
mermaid_css = open(os.path.join(TOOLS_DIR, 'mermaid.css'), encoding='utf-8').read()


n_docs = len([f for f in files if re.match(r'^\d\d-', f)])
def _body_chars(txt):
    txt = re.sub(r'```.*?```', '', txt, flags=re.S)
    txt = re.sub(r'^\|.*$', '', txt, flags=re.M)
    return len(re.findall(r'[一-鿿]', txt))
total_chars = sum(_body_chars(open(os.path.join(DOCS_DIR, f), encoding='utf-8').read()) for f in files if re.match(r'^\d\d-', f))

CSS = """
:root{--fg:#1f2428;--muted:#6b7480;--bg:#fff;--bg2:#f6f7f9;--line:#e4e8ee;--accent:#2f5fb3;--accent-bg:#eaf0fb;--code:#f4f6f8;--w:820px}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:16px}
body{margin:0;background:var(--bg);color:var(--fg);
  font:16px/1.85 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
#layout{display:flex;align-items:flex-start}
#sidebar{position:sticky;top:0;height:100vh;overflow-y:auto;flex:0 0 300px;
  background:var(--bg2);border-right:1px solid var(--line);padding:22px 0 60px;font-size:13px}
#sidebar h2{margin:0 20px 6px;font-size:15px;letter-spacing:.01em;line-height:1.4}
#sidebar .sub{margin:0 20px 14px;font-size:12px;color:var(--muted);line-height:1.6}
#filter{width:calc(100% - 40px);margin:0 20px 10px;padding:7px 10px;font-size:13px;
  border:1px solid var(--line);border-radius:6px;background:#fff;font-family:inherit}
#sidebar ul{list-style:none;margin:0;padding:0}
#sidebar a{border:0}
#sidebar .nav-part>button{display:block;width:100%;text-align:left;background:none;border:0;cursor:pointer;
  padding:9px 20px 5px;margin-top:6px;font:inherit;font-size:12px;font-weight:700;letter-spacing:.06em;
  color:var(--muted)}
#sidebar .nav-part>button::before{content:"▸";display:inline-block;width:12px;font-size:10px;transition:transform .15s}
#sidebar .nav-part.open>button::before{transform:rotate(90deg)}
#sidebar .nav-part>ul{display:none}
#sidebar .nav-part.open>ul,#sidebar.filtering .nav-part>ul{display:block}
#sidebar .nav-doc>a{display:block;padding:4px 20px 4px 32px;color:var(--fg);text-decoration:none;
  font-size:13px;border-left:3px solid transparent;line-height:1.5}
#sidebar .nav-doc>a:hover{background:#eceff3}
#sidebar .nav-doc>a.active{border-left-color:var(--accent);color:var(--accent);background:var(--accent-bg);font-weight:600}
#sidebar .nav-sub{display:none;padding:2px 0 6px}
#sidebar .nav-doc.open .nav-sub{display:block}
#sidebar .nav-sub a{display:block;padding:2px 20px 2px 46px;color:var(--muted);text-decoration:none;font-size:12px;line-height:1.5}
#sidebar .nav-sub a:hover{color:var(--accent)}
main{flex:1 1 auto;min-width:0;padding:0 48px 120px;max-width:calc(var(--w) + 96px);margin:0 auto}
.doc{padding-top:56px;border-top:1px solid var(--line);margin-top:56px}
.doc:first-of-type{border-top:0;margin-top:0;padding-top:40px}
.eyebrow{font-size:12.5px;letter-spacing:.08em;color:var(--muted);font-weight:600;margin:0 0 .4em}
h1.doc-title{font-size:30px;line-height:1.35;margin:0 0 .7em;letter-spacing:-.01em;font-weight:700}
h2{font-size:21px;margin:2.2em 0 .8em;padding-bottom:.3em;border-bottom:1px solid var(--line);font-weight:700;line-height:1.4}
h3{font-size:17px;margin:1.8em 0 .5em;font-weight:700}
h4{font-size:15.5px;margin:1.4em 0 .4em;color:var(--muted)}
p,li{overflow-wrap:break-word}
p{margin:0 0 1em}
li{margin:.15em 0}
blockquote{margin:1.3em 0;padding:.7em 1.1em;border-left:3px solid #c9d3e0;background:var(--bg2);color:#3b4453}
blockquote p:first-child{margin-top:0}blockquote p:last-child{margin-bottom:0}
blockquote.lede{border-left:3px solid var(--accent);background:var(--accent-bg);color:#2b3442;border-radius:0 8px 8px 0;padding:.9em 1.2em;font-size:15px;line-height:1.8}
code{background:var(--code);padding:.1em .35em;border-radius:4px;font-size:.87em;
  font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace}
pre{background:var(--code);padding:14px 16px;border-radius:8px;overflow-x:auto;
  font-size:13px;line-height:1.6;border:1px solid var(--line);margin:1.2em 0}
pre code{background:none;padding:0;font-size:inherit}
.tw{overflow-x:auto;margin:1.3em 0}
table{border-collapse:collapse;font-size:14px;min-width:100%;line-height:1.6}
th,td{border:0;border-bottom:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
th{background:var(--bg2);font-weight:600;white-space:nowrap;border-bottom:2px solid #d4dae3}
tbody tr:nth-child(even) td{background:#fafbfc}
a{color:var(--accent);text-decoration:none;border-bottom:1px solid #c5d3ea}
a.ext,a[title^="外部文件"]{color:var(--muted);border-bottom-style:dotted;cursor:help}
a:hover{border-bottom-color:var(--accent)}
hr{border:0;border-top:1px solid var(--line);margin:2.2em 0}
strong{font-weight:700}
/* 图 */
figure.fig{margin:1.8em 0;text-align:center}
figure.fig .mermaid{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 10px;cursor:zoom-in;
  display:flex;justify-content:center;overflow-x:auto;min-height:60px}
figure.fig .mermaid svg{max-width:100%;height:auto}
figure.fig figcaption{font-size:12.5px;color:var(--muted);margin-top:.5em;letter-spacing:.04em}
figure.fig .mermaid:not([data-processed]){font:12px/1.5 monospace;text-align:left;color:var(--muted);white-space:pre;display:block}
@media (min-width:1300px){figure.fig{margin-left:-90px;margin-right:-90px}}
/* 图放大：遮罩里居中，滚轮缩放，放大超出视口后可滚动 */
#zoom{position:fixed;inset:0;background:rgba(20,24,30,.8);display:none;z-index:50;overflow:auto;cursor:zoom-out}
#zoom.on{display:block}
#zoom .wrap{min-width:100%;min-height:100%;display:flex;align-items:center;justify-content:center;padding:40px 40px 64px}
#zoom .box{background:#fff;border-radius:10px;padding:24px;cursor:grab;flex:none;user-select:none}
#zoom .box:active{cursor:grabbing}
#zoom .box svg{display:block;max-width:none!important}
#zoom .cap{position:fixed;left:50%;transform:translateX(-50%);bottom:14px;color:#e6eaf0;font-size:13px;pointer-events:none;background:rgba(20,24,30,.85);padding:6px 14px;border-radius:999px;white-space:nowrap}
/* 上一篇 / 下一篇 */
nav.pn{display:flex;justify-content:space-between;gap:16px;margin-top:3.5em;padding-top:1.2em;border-top:1px solid var(--line);font-size:14px}
nav.pn a{border:0;color:var(--muted)}nav.pn a:hover{color:var(--accent)}
nav.pn .next{margin-left:auto;text-align:right}
#top{position:fixed;right:22px;bottom:22px;width:40px;height:40px;border-radius:50%;
  border:1px solid var(--line);background:#fff;color:var(--muted);cursor:pointer;
  font-size:17px;box-shadow:0 2px 10px rgba(0,0,0,.09);display:none}
@media (max-width:1000px){
  #layout{display:block}
  #sidebar{position:static;height:auto;width:100%;flex:none;border-right:0;border-bottom:1px solid var(--line);max-height:44vh}
  main{padding:0 20px 80px}
}
@media print{
  #sidebar,#top,#zoom,nav.pn{display:none}
  main{max-width:none;padding:0}
  .doc{page-break-before:always;border-top:0;margin-top:0}
  .doc:first-of-type{page-break-before:avoid}
  a{color:inherit;border:0}
  pre,table,figure,blockquote{page-break-inside:avoid}
  figure.fig{margin-left:0;margin-right:0}
  figure.fig .mermaid{border:0}
}
""" + mermaid_css

JS = """
mermaid.initialize(Object.assign({startOnLoad:false,securityLevel:'loose'}, MERMAID_CONFIG));
mermaid.run({querySelector:'figure.fig .mermaid'});
// 宽表格套一层横向滚动容器，正文永不横向滚动
document.querySelectorAll('main table').forEach(function(t){
  var w=document.createElement('div'); w.className='tw';
  t.parentNode.insertBefore(w,t); w.appendChild(t);
});
// 目录：当前篇高亮、展开小节、展开所在部分
var docs=[].slice.call(document.querySelectorAll('section.doc'));
var links=[].slice.call(document.querySelectorAll('#sidebar .nav-doc>a'));
var sidebar=document.getElementById('sidebar');
var lastCur=-1;
function sync(){
  var y=window.scrollY+140,cur=0;
  for(var i=0;i<docs.length;i++){ if(docs[i].offsetTop<=y) cur=i; }
  if(cur!==lastCur){
    lastCur=cur;
    links.forEach(function(a,i){
      var on=i===cur;
      a.classList.toggle('active',on);
      a.parentNode.classList.toggle('open',on);
      if(on){
        var part=a.closest('.nav-part');
        if(part && !part.classList.contains('open')){
          document.querySelectorAll('#sidebar .nav-part.open').forEach(function(p){p.classList.remove('open');});
          part.classList.add('open');
        }
        var r=a.getBoundingClientRect(), sr=sidebar.getBoundingClientRect();
        if(r.top<sr.top+40||r.bottom>sr.bottom-40) a.scrollIntoView({block:'center'});
      }
    });
  }
  document.getElementById('top').style.display=window.scrollY>600?'block':'none';
}
window.addEventListener('scroll',sync,{passive:true});
window.addEventListener('load',sync);
document.querySelectorAll('#sidebar .nav-part>button').forEach(function(b){
  b.addEventListener('click',function(){ b.parentNode.classList.toggle('open'); });
});
document.getElementById('top').onclick=function(){window.scrollTo({top:0,behavior:'smooth'});};
// 目录过滤：命中的篇目显示，所有部分临时展开
document.getElementById('filter').addEventListener('input',function(e){
  var q=e.target.value.trim().toLowerCase();
  sidebar.classList.toggle('filtering',!!q);
  document.querySelectorAll('#sidebar .nav-doc').forEach(function(li){
    li.style.display = !q || li.firstChild.textContent.toLowerCase().indexOf(q)>=0 ? '' : 'none';
  });
});
// 图放大：点图在遮罩里居中显示；滚轮以指针为中心缩放；超出视口后可滚动
var zoom=document.getElementById('zoom'), zwrap=zoom.querySelector('.wrap'), zbox=zoom.querySelector('.box'), zcap=zoom.querySelector('.cap');
var zsvg=null, zw=0, zh=0, zk=1, zlabel='';
function zapply(){
  zsvg.setAttribute('width',Math.round(zw*zk)); zsvg.setAttribute('height',Math.round(zh*zk));
  zcap.textContent=zlabel+' · '+Math.round(zk*100)+'%　滚轮缩放 · 拖动平移 · 点击空白处或按 Esc 关闭';
}
document.querySelectorAll('figure.fig .mermaid').forEach(function(m){
  m.addEventListener('click',function(){
    var svg=m.querySelector('svg'); if(!svg) return;
    var vb=svg.viewBox.baseVal; zw=Math.max(vb.width,200); zh=Math.max(vb.height,100);
    zsvg=svg.cloneNode(true); zsvg.removeAttribute('style'); zsvg.setAttribute('preserveAspectRatio','xMidYMid meet');
    zbox.innerHTML=''; zbox.appendChild(zsvg);
    var cap=m.parentNode.querySelector('figcaption'); zlabel=cap?cap.textContent:'';
    // 初始比例：整张图放进视口，小图放大到最多 1.6 倍，大图最多缩到 0.75 倍
    var fit=Math.min((window.innerWidth-130)/zw,(window.innerHeight-170)/zh);
    zk=Math.max(0.75,Math.min(1.6,fit));
    zapply(); zoom.classList.add('on'); document.body.style.overflow='hidden';
    zoom.scrollTop=0; zoom.scrollLeft=0;
  });
});
function zclose(){ zoom.classList.remove('on'); document.body.style.overflow=''; }
zoom.addEventListener('click',function(e){ if(!zbox.contains(e.target)) zclose(); });
zoom.addEventListener('wheel',function(e){
  if(!zsvg) return; e.preventDefault();
  var r=zbox.getBoundingClientRect();
  // 指针在图内的相对位置（0..1），缩放后保持该点不动
  var px=(e.clientX-r.left)/r.width, py=(e.clientY-r.top)/r.height;
  var k0=zk; zk=Math.min(6,Math.max(0.3,zk*(e.deltaY<0?1.12:1/1.12)));
  if(zk===k0) return;
  var sl=zoom.scrollLeft, st=zoom.scrollTop;
  zapply();
  var r2=zbox.getBoundingClientRect();
  var nx=r2.left+px*r2.width, ny=r2.top+py*r2.height;
  zoom.scrollLeft=sl+(nx-e.clientX); zoom.scrollTop=st+(ny-e.clientY);
},{passive:false});
document.addEventListener('keydown',function(e){ if(e.key==='Escape') zclose(); });
// 拖动平移（放大超出视口时）
var zdrag=null;
zbox.addEventListener('mousedown',function(e){ if(e.button!==0) return; zdrag={x:e.clientX,y:e.clientY,sl:zoom.scrollLeft,st:zoom.scrollTop,moved:false}; e.preventDefault(); });
window.addEventListener('mousemove',function(e){ if(!zdrag) return; zoom.scrollLeft=zdrag.sl-(e.clientX-zdrag.x); zoom.scrollTop=zdrag.st-(e.clientY-zdrag.y); if(Math.abs(e.clientX-zdrag.x)+Math.abs(e.clientY-zdrag.y)>3) zdrag.moved=true; });
window.addEventListener('mouseup',function(){ zdrag=null; });
"""

doc = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{BOOK_TITLE}</title>
<style>{CSS}</style>
</head>
<body>
<div id="layout">
<nav id="sidebar">
  <h2>{BOOK_TITLE}</h2>
  <div class="sub">{n_docs} 篇 · 约 {total_chars/10000:.0f} 万字 · 单文件离线版</div>
  <input id="filter" type="search" placeholder="过滤篇目…" autocomplete="off">
  <ul>{''.join(nav)}</ul>
</nav>
<main>
{chr(10).join(sections)}
</main>
</div>
<button id="top" title="回到顶部">↑</button>
<div id="zoom"><div class="wrap"><div class="box"></div></div><div class="cap"></div></div>
<script>{mermaid_src}</script>
<script>var MERMAID_CONFIG={mermaid_cfg};</script>
<script>{JS}</script>
</body>
</html>
"""

open(OUT, 'w', encoding='utf-8').write(doc)
print(f'{OUT}  {len(doc.encode("utf-8"))/1048576:.2f} MB  ({n_docs} 篇正文 + README/STYLE/FIGURE-GUIDE/OUTLINE)')
