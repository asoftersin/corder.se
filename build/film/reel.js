'use strict';
/* corder: 15 s brand film for corder.se. One timeline at 128 BPM (8 bars = 15 s), every frame drawn in code.
   render.mjs calls reel.init() and then reel.frame(n). Open reel.html#play for a realtime preview with sound. */

const W = 1920, H = 1080, CX = W / 2, CY = H / 2, TAU = Math.PI * 2;
const BPM = 128, BEAT = 60 / BPM, BAR = 4 * BEAT, DUR = 15;
const bt = (bar, beat = 0) => (bar - 1) * BAR + beat * BEAT;   // same grid as music.py

const P = {
  ink: [17, 17, 17], night: [11, 11, 11], paper: [255, 255, 255], stone: [244, 244, 242], warm: [234, 233, 228],
  muted: [138, 138, 138], svart: [28, 28, 28], bla: [74, 102, 132], lila: [185, 189, 240], persika: [245, 164, 147], gron: [61, 81, 67],
};
const FONT = '"Inter Tight"', MARK = 'Jost';

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => x < a ? a : x > b ? b : x;
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t0, t1, t) => clamp((t - t0) / (t1 - t0));
const E = {
  lin: t => t,
  inQuad: t => t * t,
  outCubic: t => 1 - (1 - t) ** 3,
  inCubic: t => t * t * t,
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2,
  outExpo: t => t >= 1 ? 1 : 1 - 2 ** (-10 * t),
  inExpo: t => t <= 0 ? 0 : 2 ** (10 * t - 10),
  inOutExpo: t => t <= 0 ? 0 : t >= 1 ? 1 : t < .5 ? 2 ** (20 * t - 10) / 2 : (2 - 2 ** (-20 * t + 10)) / 2,
  outBack: (t, s = 1.70158) => 1 + (s + 1) * (t - 1) ** 3 + s * (t - 1) ** 2,
  inBack: (t, s = 1.70158) => (s + 1) * t * t * t - s * t * t,
  outElastic: t => t <= 0 ? 0 : t >= 1 ? 1 : 2 ** (-10 * t) * Math.sin((t * 10 - .75) * TAU / 3) + 1,
};
const ez = (t0, t1, t, f = E.outExpo, ...a) => f(prog(t0, t1, t), ...a);
const after = (t, t0, rate) => t >= t0 ? Math.exp(-(t - t0) * rate) : 0;
const bump = (t, t0, w) => Math.exp(-((t - t0) ** 2) / (2 * w * w));
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453123; return s - Math.floor(s); };
const noise1 = x => { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i), hash(i + 1), u) * 2 - 1; };
const css = (c, a = 1) => a >= 1 ? `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})` : `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${Math.max(0, a)})`;
const mixc = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

// ---------- state ----------
let S = 1, FPS = 60, SUB = 6, out, octx, sub, sctx, acc, actx, grain, vignette, phoneC;
const IMG = {};

// ---------- drawing helpers ----------
const fillBg = (ctx, c, a = 1) => { ctx.fillStyle = css(c, a); ctx.fillRect(-120, -120, W + 240, H + 240); };
const setFont = (ctx, wght, size, fam = FONT) => { ctx.font = `${Math.round(clamp(wght, 1, 1000))} ${size}px ${fam}`; };
function layout(ctx, text, track) {
  let x = 0;
  const glyphs = [];
  for (const ch of text) { const w = ctx.measureText(ch).width; glyphs.push({ ch, x, w }); x += w + track; }
  return { glyphs, width: x - track };
}
function circle(ctx, x, y, r, c, a = 1) {
  if (r <= 0) return;
  ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fillStyle = css(c, a); ctx.fill();
}
function drawCut(ctx, img, x, y, h, { rot = 0, sx = 1, sy = 1, alpha = 1 } = {}) {
  const w = h * img.width / img.height;
  ctx.save();
  ctx.globalAlpha *= alpha;
  ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sx, sy);
  ctx.drawImage(img, -w / 2, -h / 2, w, h);
  ctx.restore();
}
function shadow(ctx, x, y, rx, ry, a) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, rx);
  g.addColorStop(0, `rgba(0,0,0,${a})`); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx); ctx.translate(-x, -y);
  ctx.fillStyle = g; ctx.fillRect(x - rx, y - rx, rx * 2, rx * 2);
  ctx.restore();
}
// Letters rising out of a mask, staggered. Returns the laid-out width.
function rise(ctx, text, x, base, size, wght, t0, t, o = {}) {
  const { color = P.ink, alpha = 1, track = -.025 * size, stagger = .028, dur = .55, align = 'left', fam = FONT, out = null } = o;
  setFont(ctx, wght, size, fam);
  const L = layout(ctx, text, track);
  const x0 = align === 'center' ? x - L.width / 2 : align === 'right' ? x - L.width : x;
  ctx.save();
  ctx.beginPath(); ctx.rect(x0 - size, base - size * 1.08, L.width + size * 2, size * 1.36); ctx.clip();
  ctx.fillStyle = css(color, alpha);
  L.glyphs.forEach((g, i) => {
    const p = E.outExpo(prog(t0 + i * stagger, t0 + i * stagger + dur, t));
    const q = out ? E.inCubic(prog(out + i * stagger * .5, out + i * stagger * .5 + .22, t)) : 0;
    if (p <= 0 || q >= 1) return;
    ctx.fillText(g.ch, x0 + g.x, base + (1 - p) * size * 1.15 - q * size * 1.15);
  });
  ctx.restore();
  return L.width;
}
function caps(ctx, text, x, y, size, color, alpha, align = 'left', spacing = .22) {
  setFont(ctx, 600, size);
  ctx.letterSpacing = `${size * spacing}px`;
  ctx.textAlign = align;
  ctx.fillStyle = css(color, alpha);
  ctx.fillText(text, x, y);
  ctx.letterSpacing = '0px';
  ctx.textAlign = 'left';
}

// ---------- 1. drop test (bar 1) ----------
const DI = [bt(1, 1), bt(1, 2), bt(1, 2.5)];        // impacts on beat 2, beat 3 and the "and" of 3
const DH = [1120, 170, 40];
const FY = 905, PH = 600, PX = CX + 360;
function dropState(t) {
  let h, rot;
  if (t < DI[0]) { const u = t / DI[0]; h = DH[0] * (1 - u * u); rot = lerp(-.62, .07, u); }
  else if (t < DI[1]) { const u = (t - DI[0]) / (DI[1] - DI[0]); h = 4 * DH[1] * u * (1 - u); rot = lerp(.07, -.03, u) - .11 * Math.sin(Math.PI * u); }
  else if (t < DI[2]) { const u = (t - DI[1]) / (DI[2] - DI[1]); h = 4 * DH[2] * u * (1 - u); rot = lerp(-.03, 0, u) + .03 * Math.sin(Math.PI * u); }
  else { h = 0; rot = .022 * Math.exp(-(t - DI[2]) * 7) * Math.sin((t - DI[2]) * 38); }
  let q = 0;
  DI.forEach((ti, k) => { q = Math.max(q, bump(t, ti + .012, .02) * [1, .55, .3][k]); });
  const sy = 1 - .08 * q, sx = 1 + .045 * q;
  return { x: PX, y: FY - PH / 2 * sy - h, h, rot, sx, sy };
}
function sceneDrop(ctx, t) {
  const push = ez(bt(1, 3.5), bt(2), t, E.inExpo);
  ctx.save();
  ctx.translate(PX, CY); ctx.scale(1 + push * .7, 1 + push * .7); ctx.translate(-PX, -CY);
  sceneDropBody(ctx, t);
  ctx.restore();
  if (push > 0) fillBg(ctx, P.paper, push);
}
function sceneDropBody(ctx, t) {
  const g = ctx.createRadialGradient(CX + 200, 380, 40, CX + 200, 380, 1300);
  g.addColorStop(0, '#3c3c3f'); g.addColorStop(1, '#121213');
  ctx.fillStyle = g; ctx.fillRect(-120, -120, W + 240, H + 240);

  const st = dropState(t);
  // floor ripples and dust at each impact
  DI.forEach((ti, k) => {
    const tau = t - ti, a = [1, .6, .35][k];
    if (tau < 0 || tau > .7) return;
    const p = E.outExpo(tau / .7);
    ctx.save(); ctx.translate(PX, FY + 4); ctx.scale(1, .13);
    ctx.beginPath(); ctx.arc(0, 0, 150 + 950 * p, 0, TAU);
    ctx.strokeStyle = `rgba(255,255,255,${.32 * a * (1 - p)})`; ctx.lineWidth = 2 / .13 * .55; ctx.stroke();
    ctx.restore();
    for (let i = 0; i < 16; i++) {
      const dir = i % 2 ? 1 : -1, v = 280 + 520 * hash(i + k * 31), vy = 260 + 420 * hash(i * 3.3 + k);
      const x = PX + dir * (90 + v * tau), y = FY - (vy * tau - 1500 * tau * tau);
      if (y > FY) continue;
      circle(ctx, x, y, (1.5 + 2.5 * hash(i * 7.1)) * a, P.paper, .5 * (1 - tau / .7));
    }
  });
  // shadow tightens as the phone gets closer to the floor
  const near = clamp(st.h / 700);
  shadow(ctx, PX, FY + 8, lerp(190, 320, near), lerp(34, 60, near), lerp(.6, .08, near));

  // phone with a moving sheen, rendered into its own buffer
  const img = IMG['17p-skogsgron'], pw = PH * img.width / img.height;
  const pc = phoneC.getContext('2d');
  pc.setTransform(S, 0, 0, S, 0, 0);
  pc.globalCompositeOperation = 'copy';
  pc.drawImage(img, 0, 0, pw, PH);
  pc.globalCompositeOperation = 'source-atop';
  const sw = ez(DI[2] + .05, DI[2] + .65, t, E.inOutCubic);
  if (sw > 0 && sw < 1) {
    const sx = lerp(-pw * 1.2, pw * 2.2, sw);
    const lg = pc.createLinearGradient(sx - 160, 0, sx + 160, PH * .4);
    lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(.5, 'rgba(255,255,255,.28)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    pc.fillStyle = lg; pc.fillRect(0, 0, pw, PH);
  }
  pc.globalCompositeOperation = 'source-over';
  ctx.save();
  ctx.translate(st.x, st.y); ctx.rotate(st.rot); ctx.scale(st.sx, st.sy);
  ctx.drawImage(phoneC, 0, 0, phoneC.width, phoneC.height, -pw / 2, -PH / 2, pw, PH);
  ctx.restore();

  // copy
  const la = ez(DI[1], DI[1] + .4, t);
  caps(ctx, 'CORDER TPU-SKAL', 250 + (1 - la) * -30, 430, 19, P.paper, .55 * la);
  rise(ctx, 'Stötdämpande', 250, 575, 128, 300, DI[1] + .02, t, { color: P.paper, stagger: .018, dur: .42 });
  rise(ctx, 'och formstabilt.', 250, 715, 128, 300, DI[2] - .02, t, { color: [150, 150, 150], stagger: .016, dur: .42 });
}

// ---------- 2. kinetic type (bar 2) ----------
function sceneType(ctx, t) {
  const T = [bt(2), bt(2, 1), bt(2, 2), bt(2, 3)];
  if (t < T[1]) {                                                   // "Bra": weight morph
    fillBg(ctx, P.paper);
    const lt = t - T[0];
    const wg = lerp(100, 820, E.outExpo(clamp(lt / .32)));
    const sc = lerp(1.18, 1, E.outExpo(clamp(lt / .4)));
    setFont(ctx, wg, 560);
    const L = layout(ctx, 'Bra', -14);
    ctx.save(); ctx.translate(CX, CY); ctx.scale(sc, sc);
    ctx.fillStyle = css(P.ink);
    L.glyphs.forEach(g => ctx.fillText(g.ch, -L.width / 2 + g.x, 560 * .727 / 2));
    ctx.restore();
  } else if (t < T[2]) {                                            // "mobiltillbehör.": letters drop in
    fillBg(ctx, P.ink);
    const lt = t - T[1];
    setFont(ctx, 600, 100);
    const fit = Math.min(250, 1720 / (layout(ctx, 'mobiltillbehör.', -2.5).width / 100));
    setFont(ctx, 600, fit);
    const L = layout(ctx, 'mobiltillbehör.', -fit * .025);
    const x0 = CX - L.width / 2, base = CY + fit * .32;
    ctx.fillStyle = css(P.paper);
    L.glyphs.forEach((g, i) => {
      const p = clamp((lt - i * .016) / .3);
      if (p <= 0) return;
      const y = base - (1 - E.outBack(p, 2.2)) * 260;
      ctx.save(); ctx.globalAlpha = clamp(p * 4);
      ctx.translate(x0 + g.x + g.w / 2, y); ctx.rotate((1 - E.outCubic(p)) * (i % 2 ? .4 : -.4));
      ctx.fillText(g.ch, -g.w / 2, 0);
      ctx.restore();
    });
  } else if (t < T[3]) {                                            // "Ännu bättre": converge
    fillBg(ctx, P.persika);
    const lt = t - T[2];
    setFont(ctx, 300, 250);
    const a = layout(ctx, 'Ännu', -6), b = layout(ctx, 'bättre', -6), gap = 70;
    const total = a.width + gap + b.width, xa = CX - total / 2, xb = xa + a.width + gap;
    const p = E.outExpo(clamp(lt / .34)), base = CY + 92;
    ctx.fillStyle = css(P.ink);
    a.glyphs.forEach(g => ctx.fillText(g.ch, xa + g.x - (1 - p) * 1100, base));
    b.glyphs.forEach(g => ctx.fillText(g.ch, xb + g.x + (1 - p) * 1100, base));
  } else {                                                          // "priser." and the full stop becomes a dot
    fillBg(ctx, P.gron);
    const lt = t - T[3];
    const sc = lerp(1.35, 1, E.outExpo(clamp(lt / .3)));
    setFont(ctx, 800, 420);
    const L = layout(ctx, 'priser.', -12);
    const x0 = CX - L.width / 2, base = CY + 150;
    ctx.save(); ctx.translate(CX, CY); ctx.scale(sc, sc); ctx.translate(-CX, -CY);
    ctx.fillStyle = css(P.paper);
    L.glyphs.forEach(g => ctx.fillText(g.ch, x0 + g.x, base));
    ctx.restore();
    const dot = L.glyphs[L.glyphs.length - 1];
    const dx = CX + (x0 + dot.x + dot.w / 2 - CX) * sc, dy = CY + (base - 420 * .066 - CY) * sc;
    const grow = ez(bt(2, 3.5), bt(3), t, E.inExpo);
    circle(ctx, dx, dy, lerp(420 * .075 * sc, 2400, grow) * (grow > 0 ? 1 : 0), P.stone);
  }
}

// ---------- 3. one case, five colours (bar 3) ----------
const COLS = [
  { name: 'Svart', c: P.svart, img: '16p-black' },
  { name: 'Blå', c: P.bla, img: '16p-blue' },
  { name: 'Lila', c: P.lila, img: '16p-purple' },
  { name: 'Persika', c: P.persika, img: '16p-pink' },
  { name: 'Skogsgrön', c: P.gron, img: null },
];
const CASE_X = 1330, CASE_Y = CY + 10;
function sceneColors(ctx, t) {
  const T = [0, 1, 2, 3].map(k => bt(3, k));
  let k = 0;
  for (let i = 1; i < 4; i++) if (t >= T[i]) k = i;
  // tinted backdrop with a radial wipe for each new colour
  fillBg(ctx, mixc(P.stone, COLS[Math.max(0, k - 1)].c, .17));
  circle(ctx, CASE_X, CASE_Y, k === 0 ? 2400 : ez(T[k], T[k] + .45, t) * 2400, mixc(P.stone, COLS[k].c, .17));

  // slot-machine swap: old case leaves upwards, new one arrives from below
  shadow(ctx, CASE_X, CASE_Y + 395, 230, 40, .22);
  for (let i = 0; i <= k; i++) {
    const inP = i === 0 ? ez(T[0], T[0] + .5, t) : ez(T[i] + .03, T[i] + .45, t);
    const outP = i < k ? ez(T[i + 1] - .06, T[i + 1] + .1, t, E.inCubic) : 0;
    if (outP >= 1) continue;
    const y = CASE_Y + (1 - inP) * 1000 - outP * 1100;
    drawCut(ctx, IMG[COLS[i].img], CASE_X, y, 740, { rot: (1 - inP) * .16 - outP * .1 });
  }

  // copy column
  const x = 200;
  caps(ctx, 'TPU-SKAL TILL IPHONE 14–16', x, 330, 18, P.ink, .55 * ez(T[0], T[0] + .4, t));
  rise(ctx, 'Ett skal.', x, 500, 150, 300, T[0], t);
  rise(ctx, 'Fem färger.', x, 668, 150, 300, T[1], t);
  // colour name rolls on every beat
  ctx.save(); ctx.beginPath(); ctx.rect(x - 10, 760, 700, 74); ctx.clip();
  for (let i = 0; i <= k; i++) {
    const inP = ez(T[i] + .07, T[i] + .4, t), outP = i < k ? ez(T[i + 1] - .02, T[i + 1] + .09, t, E.inCubic) : 0;
    const y = 815 + (1 - inP) * 74 - outP * 74;
    setFont(ctx, 600, 18, 'Menlo');
    ctx.fillStyle = css(P.muted); ctx.fillText(`0${i + 1}/05`, x, y - 4);
    setFont(ctx, 400, 54); ctx.fillStyle = css(P.ink); ctx.fillText(COLS[i].name, x + 120, y);
  }
  ctx.restore();
  // swatches; the fifth (Skogsgrön) wakes up on the last eighth
  const last = ez(bt(3, 3.5), bt(3, 3.5) + .2, t, E.outBack, 2);
  COLS.forEach((c, i) => {
    const pop = ez(T[0] + .1 + i * .04, T[0] + .45 + i * .04, t, E.outBack, 2.5);
    circle(ctx, x + 18 + i * 54, 895, 16 * pop * (i === 4 ? 1 + .25 * last : 1), c.c, i === 4 ? lerp(.35, 1, last) : 1);
  });
  const ringX = x + 18 + lerp(ringPos(t, T), 4, last) * 54;
  ctx.beginPath(); ctx.arc(ringX, 895, 24, 0, TAU);
  ctx.strokeStyle = css(P.ink, ez(T[0] + .2, T[0] + .5, t)); ctx.lineWidth = 2; ctx.stroke();
  // the green swatch floods the frame into bar 4
  const flood = ez(bt(3, 3.62), bt(4), t, E.inExpo);
  if (flood > 0) circle(ctx, x + 18 + 4 * 54, 895, flood * 2500, P.gron);
}
function ringPos(t, T) {
  let p = 0;
  for (let i = 1; i < 4; i++) p += ez(T[i], T[i] + .3, t, E.outBack, 1.8);
  return p;
}

// ---------- 4. Skogsgrön hero photo (bar 4) ----------
const PHONE_IN_PHOTO = [1268, 520];   // where the phone sits on screen at zoom 1
function sceneHero(ctx, t) {
  const T = bt(4), lt = t - T;
  fillBg(ctx, P.night);
  const img = IMG['hero-18pro'];
  const cover = Math.max(W / img.width, H / img.height);
  const settle = lerp(1.2, 1.03, E.outExpo(clamp(lt / 1.3))) + lt * .012;
  const dive = ez(bt(4, 3.45), bt(5), t, E.inExpo);
  const z = settle * lerp(1, 3.2, dive);
  const [ax, ay] = PHONE_IN_PHOTO;
  ctx.save();
  ctx.translate(ax, ay); ctx.scale(z, z); ctx.translate(-ax, -ay);
  const dw = img.width * cover, dh = img.height * cover;
  ctx.drawImage(img, (W - dw) / 2 + lerp(30, 0, E.outExpo(clamp(lt / 1.5))), (H - dh) / 2, dw, dh);
  ctx.restore();
  // a soft light sweep over the photo
  const sw = ez(T + .35, T + 1.25, t, E.inOutCubic);
  if (sw > 0 && sw < 1) {
    const x = lerp(-600, W + 600, sw);
    const lg = ctx.createLinearGradient(x - 380, 0, x + 380, 300);
    lg.addColorStop(0, 'rgba(255,255,255,0)'); lg.addColorStop(.5, 'rgba(255,255,255,.07)'); lg.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = lg; ctx.fillRect(0, 0, W, H);
  }
  // copy, exits before the dive
  const exit = bt(4, 3.15);
  caps(ctx, 'NYHET', 200, 430, 19, [168, 196, 176], ez(T + .15, T + .5, t) * (1 - ez(exit, exit + .15, t)));
  rise(ctx, 'Skogsgrön.', 200, 590, 150, 300, T + .08, t, { color: P.paper, out: exit });
  rise(ctx, 'Till iPhone 17, 17 Pro och 18 Pro.', 204, 670, 40, 300, bt(4, 1), t, { color: P.paper, alpha: .72, stagger: .008, out: exit });
  // green flood from bar 3 drains away; white flash at the end of the dive
  const flood = 1 - ez(T, T + .32, t, E.outCubic);
  if (flood > 0) fillBg(ctx, P.gron, flood);
  if (dive > .6) fillBg(ctx, P.stone, prog(.6, 1, dive));
}

// ---------- 5. lineup carousel (bar 5) ----------
const LINE = [
  { label: '18 Pro', img: '17p-skogsgron' }, { label: '17', img: '17-black' }, { label: '16', img: '16-pink' },
  { label: '15', img: '15-purple' }, { label: '14', img: '14-blue' },
];
function sceneLineup(ctx, t) {
  const T = bt(5), lt = t - T;
  fillBg(ctx, P.stone);
  let step = 0;
  for (let k = 1; k < 4; k++) step += ez(bt(5, k) - .02, bt(5, k) + .36, t, E.outBack, 1.25);
  step += ez(bt(5, 3.5) - .02, bt(5, 3.5) + .3, t, E.outBack, 1.25);
  const R = 950, F = 1500;
  const items = LINE.map((it, i) => {
    const th = (i - step) * .78;
    const enter = ez(T + i * .045, T + .5 + i * .045, t);
    const x = R * Math.sin(th) + (1 - enter) * 1500, z = R * (Math.cos(th) - 1);
    return { it, i, th, x, z, s: F / (F - z) };
  }).sort((a, b) => a.z - b.z);
  const exit = ez(bt(5, 3.75), bt(6), t, E.inExpo);
  for (const o of items) {
    const a = clamp(1.6 - Math.abs(o.th) / .9);
    if (a <= 0) continue;
    const sx = CX + o.x * o.s, sy = CY + 50;
    const h = 540 * o.s * (1 - exit * .5);
    shadow(ctx, sx, sy + h / 2 + 18, 170 * o.s, 26 * o.s, .2 * a);
    drawCut(ctx, IMG[o.it.img], sx, sy - exit * 300, h, { sx: .6 + .4 * Math.cos(o.th), alpha: a });
  }
  // headline and the model numeral under the front case
  rise(ctx, 'Skal till', 160, 175, 72, 300, T + .05, t, { out: bt(5, 3.6) });
  rise(ctx, 'iPhone 14–18 Pro.', 160, 257, 72, 300, T + .15, t, { out: bt(5, 3.6) });
  const front = Math.round(step);
  ctx.save(); ctx.beginPath(); ctx.rect(CX - 400, 868, 800, 150); ctx.clip();
  LINE.forEach((it, i) => {
    const d = i - step;
    if (Math.abs(d) > 1) return;
    setFont(ctx, 200, 120);
    ctx.textAlign = 'center'; ctx.fillStyle = css(P.ink, 1 - Math.abs(d));
    ctx.fillText(it.label, CX + d * 260, 985 + exit * 160);
  });
  ctx.restore();
  ctx.textAlign = 'left';
  void front;
  caps(ctx, 'IPHONE', CX, 870, 16, P.muted, ez(T + .3, T + .6, t) * (1 - exit), 'center');
  // dark floor rises into bar 6
  const rise6 = ez(bt(5, 3.6), bt(6), t, E.inExpo);
  if (rise6 > 0) { ctx.fillStyle = css(P.warm); ctx.fillRect(-120, H + 120 - rise6 * (H + 240), W + 240, H + 240); }
}

// ---------- 6. charging (bar 6) ----------
function cablePt(u) {   // a flowing S-curve across the frame
  const x = lerp(-80, W + 80, u);
  const y = 560 + 150 * Math.sin(u * TAU * .9 + .6) * Math.sin(u * Math.PI) + 40 * Math.sin(u * TAU * 2.3);
  return [x, y];
}
function sceneCharge(ctx, t) {
  const T = bt(6), lt = t - T;
  fillBg(ctx, P.warm);
  const exit = ez(bt(6, 3.62), bt(7), t, E.inExpo);
  ctx.save();
  ctx.translate(CX, CY); ctx.scale(1 + exit * .6, 1 + exit * .6); ctx.translate(-CX, -CY);
  // the cable line draws itself, then pulses run along it
  const draw = ez(T, T + .55, t, E.inOutCubic);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath();
  const n = 220;
  for (let i = 0; i <= n * draw; i++) { const [x, y] = cablePt(i / n); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  ctx.strokeStyle = css(P.ink); ctx.lineWidth = 9; ctx.stroke();
  ctx.setLineDash([4, 10]); ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 3; ctx.stroke(); ctx.setLineDash([]);
  if (draw >= 1 || lt > .3) {
    const pc = [P.persika, P.lila, P.bla, P.gron];
    for (let k = 0; k < 7; k++) {
      const u = ((lt - .25) * .55 + k / 7) % 1;
      if (u < 0 || u > draw) continue;
      const [x, y] = cablePt(u);
      circle(ctx, x, y, 22, pc[k % 4], .25);
      circle(ctx, x, y, 9, pc[k % 4]);
    }
  }
  // products pop in on beat 3
  const pa = ez(bt(6, 2), bt(6, 2) + .4, t, E.outBack, 1.6), pb = ez(bt(6, 2) + .08, bt(6, 2) + .48, t, E.outBack, 1.6);
  if (pa > 0) {
    shadow(ctx, 600, 905, 260, 34, .22 * clamp(pa));
    drawCut(ctx, IMG['kabel-usb-c-usb-c-2m'], 600, 690, 440 * pa, { rot: (1 - pa) * -.3 });
  }
  if (pb > 0) {
    shadow(ctx, 1330, 905, 230, 32, .22 * clamp(pb));
    drawCut(ctx, IMG['laddare-20w-dual-port'], 1330, 700, 420 * pb, { rot: (1 - pb) * .3 });
  }
  caps(ctx, 'FLÄTAD KABEL · 2 M', 600, 985, 18, P.ink, .6 * ez(bt(6, 2.4), bt(6, 2.8), t), 'center');
  caps(ctx, 'SNABBLADDARE 20W', 1330, 985, 18, P.ink, .6 * ez(bt(6, 2.5), bt(6, 2.9), t), 'center');
  ctx.restore();
  // headline
  rise(ctx, 'Laddat', CX - 30, 250, 130, 300, T + .05, t, { align: 'right', out: bt(6, 3.5) });
  rise(ctx, 'och kopplat.', CX + 10, 250, 130, 300, bt(6, 1), t, { color: P.muted, out: bt(6, 3.5) });
  if (exit > .55) fillBg(ctx, P.paper, prog(.55, 1, exit));
}

// ---------- 7. product montage on eighth notes (bar 7) ----------
const CUTS = [
  { img: 'kabel-usb-c-usb-c-2m', name: 'USB-C till USB-C', spec: '2 m · flätad', bg: P.persika, dark: false },
  { img: 'laddare-20w-usb-c', name: 'Snabbladdare 20W', spec: 'USB-C', bg: P.bla, dark: true },
  { img: '17-black', name: 'TPU-skal iPhone 17', spec: 'Svart', bg: P.gron, dark: true },
  { img: 'laddare-20w-dual-port', name: '20W Dual Port', spec: 'USB-C och USB-A', bg: P.lila, dark: false },
  { img: 'kabel-usb-a-usb-c-2m', name: 'USB-A till USB-C', spec: '2 m · flätad', bg: P.ink, dark: true },
  { img: 'laddare-18w-usb-a', name: 'Laddare 18W', spec: 'USB-A', bg: P.persika, dark: false },
  { img: 'kabel-usb-c-lightning-svart', name: 'USB-C till Lightning', spec: '2 m · svart', bg: P.stone, dark: false },
  { img: 'kabel-usb-a-lightning-2m', name: 'USB-A till Lightning', spec: '2 m · flätad', bg: P.bla, dark: true },
];
function sceneMontage(ctx, t) {
  const len = BEAT / 2, k = Math.min(7, Math.floor((t - bt(7)) / len)), lt = t - bt(7) - k * len, u = lt / len;
  const c = CUTS[k], fg = c.dark ? P.paper : P.ink;
  fillBg(ctx, c.bg);
  // giant index numeral, outlined
  setFont(ctx, 200, 760);
  ctx.lineWidth = 2; ctx.strokeStyle = css(fg, .22);
  ctx.strokeText(`0${k + 1}`, 120 - E.outExpo(u) * 40, CY + 270);
  // ring accent behind the product
  ctx.beginPath(); ctx.arc(1180, CY, 300 + 60 * E.outExpo(u), 0, TAU);
  ctx.strokeStyle = css(fg, .18); ctx.lineWidth = 2; ctx.stroke();
  const img = IMG[c.img];
  const h = Math.min(700, 760 * img.height / img.width);
  const p = E.outBack(clamp(u / .55), 1.7);
  shadow(ctx, 1180, CY + h / 2 + 30, 240, 30, .25);
  drawCut(ctx, img, 1180 + (1 - E.outExpo(u)) * (k % 2 ? 160 : -160), CY + 10, h * lerp(1.25, 1, E.outExpo(u)), { rot: (1 - p) * (k % 2 ? .35 : -.35) + lt * .15 });
  setFont(ctx, 500, 50); ctx.fillStyle = css(fg); ctx.fillText(c.name, 200, 900);
  setFont(ctx, 300, 30); ctx.fillStyle = css(fg, .7); ctx.fillText(c.spec, 200, 948);
  setFont(ctx, 400, 18, 'Menlo'); ctx.fillStyle = css(fg, .6); ctx.textAlign = 'right';
  ctx.fillText(`0${k + 1} / 08`, W - 200, 180); ctx.textAlign = 'left';
  if (k === 7) fillBg(ctx, P.paper, ez(.35, 1, u, E.inExpo));
}

// ---------- 8. end card (bar 8) ----------
function sceneEnd(ctx, t) {
  const T = bt(8), lt = t - T;
  fillBg(ctx, P.paper);
  const w = rise(ctx, 'corder', CX, CY + 40, 300, 400, T + .02, t, { fam: MARK, align: 'center', track: 2, stagger: .045, dur: .7 });
  void w;
  const sw = [P.svart, P.bla, P.lila, P.persika, P.gron];
  sw.forEach((c, i) => {
    const pop = ez(bt(8, 1) + i * BEAT / 4, bt(8, 1) + i * BEAT / 4 + .35, t, E.outBack, 2.4);
    const hop = ez(bt(8, 3) + i * .04, bt(8, 3) + i * .04 + .3, t) * (1 - ez(bt(8, 3) + i * .04 + .12, bt(8, 3) + i * .04 + .45, t, E.inOutCubic));
    circle(ctx, CX + (i - 2) * 46, CY + 135 - hop * 22, 13 * pop, c);
  });
  const ta = ez(bt(8, 1.6), bt(8, 2.4), t);
  setFont(ctx, 300, 44); ctx.textAlign = 'center'; ctx.fillStyle = css(P.ink, .78 * ta);
  ctx.fillText('Mobiltillbehör designade i Sverige.', CX, CY + 245 + (1 - ta) * 20);
  ctx.textAlign = 'left';
  caps(ctx, 'FINNS HOS GO BANANA I JÖNKÖPING OCH VIP MULLSJÖ', CX, CY + 330, 16, P.muted, ez(bt(8, 2.3), bt(8, 3), t), 'center');
  const flash = after(t, T, 9);
  if (flash > .01) fillBg(ctx, P.paper, flash);
}

// ---------- camera, motion blur and post ----------
const HITS = [
  [DI[0], .8], [DI[1], .35], [DI[2], .15], [bt(2), .5], [bt(2, 1), .35], [bt(2, 2), .35], [bt(2, 3), .5],
  [bt(3), .3], [bt(3, 1), .2], [bt(3, 2), .2], [bt(3, 3), .2], [bt(4), .6], [bt(5), .4],
  ...[1, 2, 3].map(k => [bt(5, k), .12]), [bt(6), .3], [bt(6, 2), .3],
  ...[0, 1, 2, 3, 4, 5, 6, 7].map(k => [bt(7, k / 2), .25]), [bt(8), .6],
];
const hitEnv = (t, rate) => HITS.reduce((s, [h, a]) => s + a * after(t, h, rate), 0);

function renderScene(ctx, t) {
  ctx.setTransform(S, 0, 0, S, 0, 0);
  ctx.globalAlpha = 1;
  const punch = 1 + .022 * hitEnv(t, 16), sh = 6 * hitEnv(t, 22);
  ctx.translate(CX + sh * noise1(t * 45), CY + sh * noise1(t * 45 + 70));
  ctx.scale(punch, punch);
  ctx.translate(-CX, -CY);
  if (t < bt(2)) sceneDrop(ctx, t);
  else if (t < bt(3)) sceneType(ctx, t);
  else if (t < bt(4)) sceneColors(ctx, t);
  else if (t < bt(5)) sceneHero(ctx, t);
  else if (t < bt(6)) sceneLineup(ctx, t);
  else if (t < bt(7)) sceneCharge(ctx, t);
  else if (t < bt(8)) sceneMontage(ctx, t);
  else sceneEnd(ctx, t);
}

function post(t, f) {
  octx.setTransform(1, 0, 0, 1, 0, 0);
  octx.globalCompositeOperation = 'copy';
  octx.drawImage(acc, 0, 0);
  octx.globalCompositeOperation = 'source-over';
  octx.setTransform(S, 0, 0, S, 0, 0);
  octx.fillStyle = vignette; octx.fillRect(0, 0, W, H);
  // film grain, offset deterministically per frame
  octx.save();
  octx.globalCompositeOperation = 'overlay';
  octx.globalAlpha = .05;
  octx.translate(-Math.floor(hash(f) * 256), -Math.floor(hash(f + .5) * 256));
  octx.fillStyle = grain; octx.fillRect(0, 0, W + 512, H + 512);
  octx.restore();
}

async function loadImages() {
  const names = ['16p-black', '16p-blue', '16p-purple', '16p-pink', '17p-skogsgron', '17-black', '16-pink', '15-purple', '14-blue',
    'hero-18pro', ...CUTS.map(c => c.img)];
  await Promise.all([...new Set(names)].map(n => new Promise((res, rej) => {
    const im = new Image();
    im.onload = res; im.onerror = () => rej(new Error('missing image ' + n));
    im.src = `img/${n}.webp`;
    IMG[n] = im;
  })));
}

function canvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

window.reel = {
  ready: true,
  async init(o) {
    S = o.scale; FPS = o.fps; SUB = o.sub;
    out = document.getElementById('out');
    out.width = Math.round(W * S); out.height = Math.round(H * S);
    out.style.width = out.width + 'px'; out.style.height = out.height + 'px';
    octx = out.getContext('2d');
    sub = canvas(out.width, out.height); sctx = sub.getContext('2d');
    acc = canvas(out.width, out.height); actx = acc.getContext('2d');
    await Promise.all([document.fonts.load(`300 100px ${FONT}`), document.fonts.load(`800 100px ${FONT}`), document.fonts.load(`400 100px ${MARK}`), loadImages()]);
    const img = IMG['17p-skogsgron'];
    phoneC = canvas(Math.ceil(PH * img.width / img.height * S), Math.ceil(PH * S));
    const g = canvas(256, 256), gc = g.getContext('2d'), id = gc.createImageData(256, 256);
    for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (hash(i * .37) - .5) * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
    gc.putImageData(id, 0, 0);
    grain = octx.createPattern(g, 'repeat');
    vignette = octx.createRadialGradient(CX, CY, H * .45, CX, CY, H * 1.05);
    vignette.addColorStop(0, 'rgba(0,0,0,0)'); vignette.addColorStop(1, 'rgba(0,0,0,.22)');
    return { size: [out.width, out.height], fps: FPS, sub: SUB };
  },
  async frame(f) {
    const t = f / FPS;
    for (let k = 0; k < SUB; k++) {
      const ts = SUB === 1 ? t : t + ((k + .5) / SUB - .5) * .5 / FPS;   // 180° shutter
      renderScene(sctx, clamp(ts, 0, DUR - 1e-4));
      actx.globalAlpha = 1 / (k + 1);
      actx.drawImage(sub, 0, 0);
    }
    actx.globalAlpha = 1;
    post(t, f);
    return true;
  },
};

if (location.hash === '#play') {
  addEventListener('load', async () => {
    await reel.init({ scale: Math.min(innerWidth / W, innerHeight / H), fps: 60, sub: 1 });
    const audio = new Audio('music.wav');
    reel.frame(0);
    addEventListener('click', () => {
      audio.currentTime = 0; audio.play();
      const loop = () => { if (audio.currentTime < DUR && !audio.ended) { reel.frame(Math.floor(audio.currentTime * 60)); requestAnimationFrame(loop); } };
      loop();
    });
  });
}
