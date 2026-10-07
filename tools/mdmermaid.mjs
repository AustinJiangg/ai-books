// Extract ```mermaid fences from markdown files and validate each with mermaid.parse.
import fs from 'node:fs'
const files = process.argv.slice(2)
let mermaid
try {
  const { JSDOM } = await import('jsdom')
  const dom = new JSDOM('<!doctype html><html><body></body></html>')
  global.window = dom.window; global.document = dom.window.document
  mermaid = (await import('mermaid')).default
  mermaid.initialize({ startOnLoad: false })
} catch (e) {
  console.log('SKIP (no jsdom):', e.message.split('\n')[0]); process.exit(0)
}
let bad = 0
for (const f of files) {
  const lines = fs.readFileSync(f, 'utf8').split('\n')
  let cur = null, start = 0, n = 0
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i]
    if (cur === null && /^\s*```mermaid\s*$/.test(l)) { cur = []; start = i + 1; continue }
    if (cur !== null && /^\s*```\s*$/.test(l)) {
      n++
      try { await mermaid.parse(cur.join('\n')); console.log(`OK    ${f}:${start} (block ${n})`) }
      catch (e) { bad++; console.log(`FAIL  ${f}:${start} (block ${n})\n      ${String(e.message).slice(0, 400)}`) }
      cur = null; continue
    }
    if (cur !== null) cur.push(l)
  }
  if (cur !== null) { bad++; console.log(`FAIL  ${f}: unterminated mermaid fence opened at line ${start}`) }
  if (n === 0) console.log(`----  ${f}: no mermaid blocks`)
}
process.exit(bad ? 1 : 0)
