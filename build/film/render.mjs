#!/usr/bin/env node
// Frame-accurate renderer: serves this folder, drives headless Chrome over the DevTools
// Protocol, asks the page to draw frame N, screenshots it and pipes PNGs into ffmpeg.
//
//   node render.mjs --stills=0.5,2.9 --out=stills          # review frames
//   node render.mjs --video=reel.mp4 --audio=music.wav     # full render
//   options: --fps=60 --scale=1 --sub=6 (motion-blur subframes) --from=0 --to=15 --tmp=DIR
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const opt = Object.fromEntries(process.argv.slice(2).map(a => {
  const m = a.match(/^--([^=]+)(?:=(.*))?$/);
  return [m[1], m[2] ?? '1'];
}));
const FPS = +(opt.fps ?? 60), SCALE = +(opt.scale ?? 1), SUB = +(opt.sub ?? 6);
const W = Math.round(1920 * SCALE), H = Math.round(1080 * SCALE);
const PAGE = opt.page ?? 'reel.html';
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };
const sleep = ms => new Promise(r => setTimeout(r, ms));

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'Content-Type': MIME[path.extname(p)] ?? 'application/octet-stream', 'Cache-Control': 'no-store' });
  fs.createReadStream(p).pipe(res);
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));

const profile = fs.mkdtempSync(path.join(opt.tmp ?? os.tmpdir(), 'reel-chrome-'));
const dbgPort = 9300 + Math.floor(Math.random() * 600);
const chrome = spawn(CHROME, [
  '--headless=new', `--remote-debugging-port=${dbgPort}`, `--user-data-dir=${profile}`,
  '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--mute-audio',
  '--force-color-profile=srgb', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader',
  `--window-size=${W},${H}`, 'about:blank',
], { stdio: 'ignore' });

const cleanup = async () => {
  const exited = new Promise(r => chrome.once('exit', r));
  try { chrome.kill('SIGKILL'); } catch {}
  await Promise.race([exited, sleep(3000)]);
  server.close();
  try { fs.rmSync(profile, { recursive: true, force: true, maxRetries: 5 }); } catch {}
};

let wsUrl;
for (let i = 0; i < 200 && !wsUrl; i++) {
  try {
    const list = await (await fetch(`http://127.0.0.1:${dbgPort}/json/list`)).json();
    wsUrl = list.find(t => t.type === 'page')?.webSocketDebuggerUrl;
  } catch {}
  if (!wsUrl) await sleep(100);
}
if (!wsUrl) { await cleanup(); throw new Error('Chrome did not expose a page target'); }

const ws = new WebSocket(wsUrl);
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
let seq = 0;
const waiting = new Map();
ws.onmessage = e => {
  const m = JSON.parse(e.data);
  if (m.id) {
    const w = waiting.get(m.id);
    waiting.delete(m.id);
    m.error ? w.rej(new Error(m.error.message)) : w.res(m.result);
  } else if (m.method === 'Runtime.consoleAPICalled') {
    console.log('[page]', m.params.args.map(a => a.value ?? a.description).join(' '));
  } else if (m.method === 'Runtime.exceptionThrown') {
    console.error('[page error]', m.params.exceptionDetails.exception?.description ?? m.params.exceptionDetails.text);
  }
};
const send = (method, params = {}) => new Promise((res, rej) => {
  const id = ++seq;
  waiting.set(id, { res, rej });
  ws.send(JSON.stringify({ id, method, params }));
});
const evaluate = async expression => {
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? r.exceptionDetails.text);
  return r.result.value;
};
const shot = async () => Buffer.from((await send('Page.captureScreenshot', {
  format: 'png', clip: { x: 0, y: 0, width: W, height: H, scale: 1 }, optimizeForSpeed: true,
})).data, 'base64');

try {
  await send('Runtime.enable');
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Page.navigate', { url: `http://127.0.0.1:${server.address().port}/${PAGE}` });
  for (let i = 0; i < 300; i++) {
    if (await evaluate('!!(window.reel && window.reel.ready)').catch(() => false)) break;
    await sleep(100);
  }
  const info = await evaluate(`reel.init(${JSON.stringify({ scale: SCALE, fps: FPS, sub: SUB })})`);
  console.log('init', JSON.stringify(info));

  if (opt.stills) {
    const out = path.resolve(opt.out ?? 'stills');
    fs.mkdirSync(out, { recursive: true });
    for (const s of opt.stills.split(',')) {
      const f = Math.round(+s * FPS);
      await evaluate(`reel.frame(${f})`);
      const file = path.join(out, `t${(+s).toFixed(3)}.png`);
      fs.writeFileSync(file, await shot());
      console.log('wrote', file);
    }
  }

  if (opt.video) {
    const f0 = Math.round(+(opt.from ?? 0) * FPS), f1 = Math.round(+(opt.to ?? 15) * FPS);
    const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-'];
    if (opt.audio) args.push('-ss', String(f0 / FPS), '-i', path.resolve(opt.audio));
    args.push('-c:v', 'libx264', '-preset', opt.preset ?? 'slow', '-crf', opt.crf ?? '14', '-pix_fmt', 'yuv420p',
      '-profile:v', 'high', '-movflags', '+faststart');
    if (opt.audio) args.push('-c:a', 'aac', '-b:a', '320k', '-shortest');
    args.push(path.resolve(opt.video));
    const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exited ' + c))));
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      await evaluate(`reel.frame(${f})`);
      const png = await shot();
      if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - f0) % 60 === 59) {
        const el = (Date.now() - t0) / 1000, per = el / (f - f0 + 1);
        console.log(`frame ${f + 1}/${f1}  ${per.toFixed(2)}s/frame  eta ${Math.round(per * (f1 - f - 1))}s`);
      }
    }
    ff.stdin.end();
    await done;
    console.log('wrote', path.resolve(opt.video), `in ${Math.round((Date.now() - t0) / 1000)}s`);
  }
} finally {
  ws.close();
  await cleanup();
}
