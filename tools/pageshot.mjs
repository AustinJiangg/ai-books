// 打包页截图（验收用）：node pageshot.mjs <html 绝对路径> <out.png> [#doc--NN-xxx] [视口高度]；需 LD_LIBRARY_PATH 同 figcheck.sh
import { chromium } from 'playwright-chromium';
const [htmlPath, out, anchor, tall] = process.argv.slice(2);
const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: tall ? +tall : 900 }, deviceScaleFactor: 1 });
await p.goto('file://' + htmlPath + (anchor || '')); await p.waitForTimeout(9000);
if (anchor) await p.evaluate(a => { location.hash = ''; location.hash = a; }, anchor);
await p.waitForTimeout(500);
await p.screenshot({ path: out }); await b.close();
