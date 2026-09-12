// 图检查：用真实 chromium + 本书的 mermaid 主题渲染 md 里的每张 mermaid 图，
// 输出自然尺寸、重叠数、溢出数，并按各书 FIGURE-GUIDE.md 的阈值给出 PASS / WARN。
// 用法: node figcheck.mjs [--png <目录>] <md 文件或目录>...
// 环境: 若系统缺 libnss3 等，先 export LD_LIBRARY_PATH=<解开的 deb 库目录>（见 FIGURE-GUIDE）
import fs from 'node:fs'; import path from 'node:path';
import { chromium } from 'playwright-chromium';
const here = path.dirname(new URL(import.meta.url).pathname);
const args = process.argv.slice(2); let png = null;
const pi = args.indexOf('--png'); if (pi >= 0) { png = args[pi + 1]; args.splice(pi, 2); fs.mkdirSync(png, { recursive: true }); }
const files = args.flatMap(a => fs.statSync(a).isDirectory()
  ? fs.readdirSync(a).filter(f => /^\d\d-.*\.md$/.test(f)).sort().map(f => path.join(a, f)) : [a]);
const cfg = fs.readFileSync(path.join(here, 'mermaid-config.json'), 'utf8');
const css = fs.readFileSync(path.join(here, 'mermaid.css'), 'utf8');
const mermaidJs = fs.readFileSync(path.join(here, 'node_modules/mermaid/dist/mermaid.min.js'), 'utf8');
const LIMITS = { maxW: 1040, maxH: 940, maxAspect: 3.2, minAspect: 0.4 };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 2 });
await page.setContent(`<html><head><style>${css}</style></head><body style="margin:0;background:#fff"><div id="w" class="mermaid" style="width:1100px;padding:16px"></div>
<script>${mermaidJs}</script><script>mermaid.initialize(Object.assign({startOnLoad:false,securityLevel:'loose'},${cfg}));</script></body></html>`);
let warn = 0, total = 0;
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8');
  const blocks = [...src.matchAll(/```mermaid\n([\s\S]*?)```/g)].map(m => m[1]);
  for (let i = 0; i < blocks.length; i++) {
    total++;
    const id = `${path.basename(f, '.md')}--${i + 1}`;
    let d;
    try {
      d = await page.evaluate(async ([code, id]) => {
        const w = document.getElementById('w'); w.innerHTML = '';
        const { svg } = await mermaid.render('m' + id.replace(/[^a-z0-9]/gi, ''), code);
        w.innerHTML = svg; const s = w.querySelector('svg');
        s.style.maxWidth = 'none'; s.style.width = s.viewBox.baseVal.width + 'px';
        const vb = s.viewBox.baseVal;
        const box = e => e.getBoundingClientRect();
        const contains = (P, Q) => P.left <= Q.left + 1 && P.right >= Q.right - 1 && P.top <= Q.top + 1 && P.bottom >= Q.bottom - 1;
        const inter = (A, B) => Math.min(A.right, B.right) - Math.max(A.left, B.left) > 3 && Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top) > 3;
        // 实体：节点形状、边标签、簇标题、时序图参与者与 note
        const items = [];
        s.querySelectorAll('.node').forEach(n => { const sh = n.querySelector('rect,polygon,circle,path,ellipse'); if (sh) items.push({ k: 'node', r: box(sh) }); });
        s.querySelectorAll('.edgeLabel').forEach(e => { const r = box(e); if (r.width > 2) items.push({ k: 'elabel', r, own: (e.querySelector('[data-id]') || e).getAttribute('data-id') }); });
        s.querySelectorAll('.cluster-label, .cluster .label').forEach(e => { const r = box(e); if (r.width > 2) items.push({ k: 'clabel', r }); });
        s.querySelectorAll('rect.actor, rect.note, .messageText, .noteText, .labelText, .loopText').forEach(e => { const r = box(e); if (r.width > 2) items.push({ k: 'seq:' + (e.getAttribute('class') || e.tagName).split(' ')[0], r }); });
        s.querySelectorAll('.stateGroup rect, .transition ~ .edgeLabel').forEach(e => { const r = box(e); if (r.width > 2) items.push({ k: 'state', r }); });
        let overlap = 0; const pairs = [];
        for (let a = 0; a < items.length; a++) for (let b = a + 1; b < items.length; b++) {
          const A = items[a].r, B = items[b].r;
          if (inter(A, B) && !contains(A, B) && !contains(B, A)) { overlap++; if (pairs.length < 4) pairs.push(items[a].k + '/' + items[b].k); }
        }
        // 边标签压在边线上：标签框与 path 采样点相交（排除标签自身所属边无法判断，粗略计数）
        let labelOnEdge = 0;
        const labels = items.filter(x => x.k === 'elabel');
        s.querySelectorAll('path.flowchart-link, path.transition, .edgePath path').forEach(p => {
          const L = p.getTotalLength(); if (!L) return;
          const m = s.getScreenCTM(); const pts = [];
          for (let t = 0; t <= L; t += 4) { const pt = p.getPointAtLength(t); pts.push([pt.x * m.a + m.e, pt.y * m.d + m.f]); }
          for (const { r: lb, own: ownId } of labels) {
            if (ownId && p.id === ownId) continue;
            const cx = (lb.left + lb.right) / 2, cy = (lb.top + lb.bottom) / 2;
            let hit = false, own = false;
            for (const [x, y] of pts) {
              if (x > lb.left + 2 && x < lb.right - 2 && y > lb.top + 2 && y < lb.bottom - 2) hit = true;
              if (Math.hypot(x - cx, y - cy) < Math.max(10, lb.height * 0.5)) own = true;
            }
            if (hit && !own) labelOnEdge++;  // 自己的边经过标签中心，不算；别的边穿过标签才算
          }
        });
        // 文本溢出节点
        let overflow = 0;
        s.querySelectorAll('.node').forEach(n => { const sh = n.querySelector('rect,polygon,circle,path,ellipse'); const lb = n.querySelector('foreignObject, .label'); if (!sh || !lb) return; const a = box(sh), t = box(lb); if (t.width > a.width + 4 || t.height > a.height + 4) overflow++; });
        return { w: Math.round(vb.width), h: Math.round(vb.height), overlap, pairs, labelOnEdge, overflow, nodes: items.filter(x => x.k === 'node').length };
      }, [blocks[i], id]);
    } catch (e) { console.log(`FAIL ${id}  ${String(e).split('\n')[0].slice(0, 120)}`); warn++; continue; }
    const why = [];
    if (d.w > LIMITS.maxW) why.push(`太宽 ${d.w}>${LIMITS.maxW}`);
    if (d.h > LIMITS.maxH) why.push(`太高 ${d.h}>${LIMITS.maxH}`);
    const asp = d.w / d.h; if (asp > LIMITS.maxAspect) why.push(`太扁 ${asp.toFixed(1)}:1`); if (asp < LIMITS.minAspect) why.push(`太窄 1:${(1 / asp).toFixed(1)}`);
    if (d.overlap) why.push(`重叠 ${d.overlap} (${d.pairs.join(',')})`);
    if (d.labelOnEdge) why.push(`标签压线 ${d.labelOnEdge}`);
    if (d.overflow) why.push(`文字溢出 ${d.overflow}`);
    if (why.length) warn++;
    console.log(`${why.length ? 'WARN' : 'PASS'} ${id}  ${d.w}x${d.h} nodes=${d.nodes}${why.length ? '  ' + why.join('; ') : ''}`);
    if (png) { await (await page.$('#w')).screenshot({ path: path.join(png, id + '.png') }); }
  }
}
await browser.close();
console.log(`\n${total} 张图，${warn} 张需处理`);
process.exit(0);
