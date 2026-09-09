// mermaid 渲染后的修补：若时序图末条消息与编号圆点贴边（mirrorActors 关闭时会发生），
// 按可见绘制元素的包围盒把 viewBox 向外扩（每边最多 40px，四周至少留 8px），只扩不缩。
// 当前 mirrorActors 已开启，正常情况下本函数不会改动任何东西，作为保险保留。
// 打包页与 figcheck 共用；参数是 <svg> 元素。
function fitMermaidSvg(svg, pad) {
  pad = pad == null ? 8 : pad;
  if (svg.getAttribute('aria-roledescription') !== 'sequence') return;  // 只有时序图会贴边裁切
  var vb = svg.viewBox.baseVal;
  if (!vb || !vb.width) return;
  var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity, n = 0;
  var els = svg.querySelectorAll('rect,circle,ellipse,path,line,polygon,polyline,text,foreignObject');
  for (var i = 0; i < els.length; i++) {
    var e = els[i];
    if (e.closest('defs') || e.closest('marker')) continue;
    var cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.opacity === '0') continue;
    var bb;
    try { bb = e.getBBox(); } catch (err) { continue; }
    if (!bb.width && !bb.height) continue;
    // 明显在画布外很远的是量字辅助元素，忽略
    if (bb.x > vb.x + vb.width + 200 || bb.y > vb.y + vb.height + 200 || bb.x + bb.width < vb.x - 200 || bb.y + bb.height < vb.y - 200) continue;
    x1 = Math.min(x1, bb.x); y1 = Math.min(y1, bb.y); x2 = Math.max(x2, bb.x + bb.width); y2 = Math.max(y2, bb.y + bb.height); n++;
  }
  if (!n) return;
  var lim = 40;
  var nx = Math.max(vb.x - lim, Math.min(vb.x, x1 - pad));
  var ny = Math.max(vb.y - lim, Math.min(vb.y, y1 - pad));
  var nx2 = Math.min(vb.x + vb.width + lim, Math.max(vb.x + vb.width, x2 + pad));
  var ny2 = Math.min(vb.y + vb.height + lim, Math.max(vb.y + vb.height, y2 + pad));
  if (nx === vb.x && ny === vb.y && nx2 === vb.x + vb.width && ny2 === vb.y + vb.height) return;
  svg.setAttribute('viewBox', nx + ' ' + ny + ' ' + (nx2 - nx) + ' ' + (ny2 - ny));
  svg.style.maxWidth = (nx2 - nx) + 'px';
  var h = svg.getAttribute('height');
  if (h && h !== '100%') svg.setAttribute('height', String(ny2 - ny));
}
