#!/usr/bin/env python3
"""Synthesises the reel soundtrack on the same 128 BPM grid as the visuals (8 bars = 15.0 s).

Everything is generated from oscillators and noise with numpy: no samples, no scipy.
Usage: python3 -I music.py out.wav
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 128
BEAT = 60 / BPM            # 0.46875 s
BAR = 4 * BEAT             # 1.875 s
DUR = 15.0
N = int(SR * (DUR + 3))    # room for reverb tails, trimmed at the end
rng = np.random.default_rng(11)

drums = np.zeros((2, N))
music = np.zeros((2, N))   # sidechained to the kick
fx = np.zeros((2, N))
send = np.zeros(N)         # reverb send
kicks = []


def b(bar, beat=0.0):
    """Time of a beat; bars are 1-indexed, beats 0-indexed (fractions allowed)."""
    return (bar - 1) * BAR + beat * BEAT


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def add(bus, sig, t, gain=1.0, pan=0.0, rev=0.0):
    i = int(round(t * SR))
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(a) * 1.414, sig * np.sin(a) * 1.414])
    n = min(sig.shape[1], N - i)
    if n <= 0:
        return
    bus[:, i:i + n] += sig[:, :n] * gain
    send[i:i + n] += sig[:, :n].mean(axis=0) * gain * rev


# ---------- filters (zero-phase FFT magnitude filters, plus an STFT sweep filter) ----------
def _resp(kind, f, fc, order=2, q=1.0):
    if kind == 'lp':
        return 1 / np.sqrt(1 + (f / fc) ** (2 * order))
    if kind == 'hp':
        return 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order))
    return np.exp(-0.5 * (np.log2(np.maximum(f, 1.0) / fc) * 2 * q) ** 2)


def filt(x, kind, fc, order=2, q=1.0, resp=None):
    nfft = 1 << (len(x) - 1).bit_length()
    f = np.fft.rfftfreq(nfft, 1 / SR)
    h = resp(f) if resp else _resp(kind, f, fc, order, q)
    return np.fft.irfft(np.fft.rfft(x, nfft) * h, nfft)[:len(x)]


def sweep(x, kind, fc_at, order=2, q=1.0, win=2048, hop=256):
    w = np.hanning(win)
    f = np.fft.rfftfreq(win, 1 / SR)
    xp = np.concatenate([x, np.zeros(win)])
    out = np.zeros(len(xp))
    norm = np.zeros(len(xp))
    for s in range(0, len(x), hop):
        H = _resp(kind, f, fc_at((s + win / 2) / SR), order, q)
        out[s:s + win] += np.fft.irfft(np.fft.rfft(xp[s:s + win] * w) * H, win) * w
        norm[s:s + win] += w * w
    return (out / np.maximum(norm, 1e-6))[:len(x)]


def noise(dur):
    return rng.standard_normal(int(dur * SR))


# ---------- instruments ----------
def kick(f0=160, f1=46, k=30, decay=6.5, click=0.5, dur=0.55):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t * k)
    body = np.tanh(1.7 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t * decay)
    clk = filt(noise(dur), 'hp', 2500) * np.exp(-t * 320) * click
    return (body + clk) * np.minimum(1, t / 0.001)


def clap(bright=1400, dur=0.4):
    t = tt(dur)
    env = sum((t >= d) * np.exp(-np.maximum(t - d, 0) * 110) for d in (0, 0.010, 0.021))
    env = env * 0.6 + (t >= 0.028) * np.exp(-np.maximum(t - 0.028, 0) * 16)
    return filt(noise(dur) * env, 'bp', bright, q=0.8) * 2.2


def hat(decay=70, dur=0.12):
    t = tt(dur)
    return filt(noise(dur), 'hp', 7500, order=3) * np.exp(-t * decay)


def pluck(m, dur=0.45, bright=1.0, detune=0.0):
    f = mtof(m) * 2 ** (detune / 1200)
    t = tt(dur)
    y = np.zeros_like(t)
    for h in range(1, int(min(28, SR * 0.45 / f)) + 1):
        y += np.sin(2 * np.pi * f * h * t) / h * np.exp(-t * (5 + 11 * h / bright))
    return y * np.minimum(1, t / 0.002)


def bass(m, dur):
    f = mtof(m)
    t = tt(dur)
    y = np.sin(2 * np.pi * f * t) + 0.45 * sum(np.sin(2 * np.pi * f * h * t) / h ** 1.6 for h in range(2, 8))
    env = np.minimum(1, t / 0.004) * np.exp(-t * 2.5) * np.clip((dur - t) / 0.015, 0, 1)
    return np.tanh(1.4 * y) * env


def pad(notes, dur, attack=0.5, release=0.7, warmth=7.0):
    t = tt(dur)
    out = np.zeros((2, len(t)))
    for m in notes:
        for cents, pan in ((-9, -0.7), (0, 0.0), (9, 0.7)):
            f = mtof(m) * 2 ** (cents / 1200)
            ph = rng.random() * 6.28
            v = sum(np.sin(2 * np.pi * f * h * t + ph * h) / h * np.exp(-h / warmth) for h in range(1, 14))
            a = (pan + 1) * np.pi / 4
            out[0] += v * np.cos(a)
            out[1] += v * np.sin(a)
    env = np.minimum(1, t / attack) ** 2 * np.clip((dur - t) / release, 0, 1)
    return out * env / (len(notes) * 2.2)


def bell(m, dur=1.6):
    f = mtof(m)
    t = tt(dur)
    parts = ((1, 1.0, 2.2), (2.76, 0.45, 4.5), (5.40, 0.25, 7.0), (8.93, 0.12, 10.0))
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in parts)
    return y * np.minimum(1, t / 0.001)


def boom(dur=1.6, f0=70, f1=32):
    t = tt(dur)
    f = f1 + (f0 - f1) * np.exp(-t * 6)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)
    thud = filt(noise(dur), 'lp', 300) * np.exp(-t * 12) * 0.8
    return np.tanh(1.5 * (body + thud))


def crash(dur=2.2, decay=2.2):
    t = tt(dur)
    l = filt(noise(dur), 'hp', 3500) * np.exp(-t * decay)
    r = filt(noise(dur), 'hp', 3500) * np.exp(-t * decay)
    return np.stack([l, r]) * np.minimum(1, t / 0.002)


def whoosh(dur, f_lo=300, f_hi=7000, curve=2.5):
    t = tt(dur)
    x = sweep(noise(dur), 'bp', lambda s: f_lo * (f_hi / f_lo) ** min(1, s / dur), q=0.7)
    env = (t / dur) ** curve * np.clip((dur - t) / 0.01, 0, 1)
    return x * env


def blip(f, dur=0.07, drop=0.5, square=False):
    t = tt(dur)
    ph = 2 * np.pi * np.cumsum(f * (1 - drop * (1 - np.exp(-t * 60)))) / SR
    s = np.sign(np.sin(ph)) * 0.5 if square else np.sin(ph)
    return s * np.exp(-t * 45) * np.minimum(1, t / 0.001)


def thock(dur=0.35):
    """A phone in a TPU case landing on a hard floor: low thump plus a damped plastic click."""
    t = tt(dur)
    f = 55 + 70 * np.exp(-t * 40)
    thump = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14)
    click = filt(noise(dur), 'bp', 2300, q=1.4) * np.exp(-t * 120) * 0.9
    return np.tanh(1.3 * (thump + click)) * np.minimum(1, t / 0.0008)


def bloop(f0, dur=0.12):
    t = tt(dur)
    fr = f0 * (1 + 1.4 * (1 - np.exp(-t * 40)))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * np.minimum(1, t / dur)) ** 2


def kick_at(t, gain=1.0, **kw):
    kicks.append(t)
    add(drums, kick(**kw), t, gain)


# ---------- arrangement ----------
CHORDS = {  # bass note, chord tones
    'Am': (45, (57, 60, 64, 67)),
    'F': (41, (53, 57, 60, 64)),
    'C': (48, (55, 60, 64, 67)),
    'G': (43, (55, 59, 62, 67)),
}
PROG = {2: 'Am', 3: 'F', 4: 'C', 5: 'G', 6: 'Am', 7: 'F'}

# Bar 1: the drop test, the phone lands on beat 2, bounces on beat 3 and the "and" of 3
add(fx, whoosh(0.47, 3500, 600, curve=0.5) * 0.22, 0.0)
add(music, pad((57, 64, 69), BAR + 0.3, attack=1.4, release=0.4, warmth=3), 0.0, 0.35)
for t, g in ((b(1, 1), 1.0), (b(1, 2), 0.55), (b(1, 2.5), 0.3)):
    add(fx, thock(), t, 0.75 * g, pan=0.25, rev=0.3)
    kick_at(t, 0.6 * g, f0=130, decay=10)
add(fx, bell(93, 1.2), b(1, 2.6), 0.05, pan=-0.3, rev=0.6)        # sheen sparkle
add(fx, whoosh(0.30, 400, 9000, curve=3.0), b(1, 3.36), 0.45)

# Bars 2-6: groove
for bar in range(2, 7):
    bass_note, tones = CHORDS[PROG[bar]]
    for beat in range(4):
        kick_at(b(bar, beat), 1.0)
        add(music, bass(bass_note, BEAT * 0.42), b(bar, beat + 0.5), 0.55)
        if beat in (1, 3):
            add(drums, clap(), b(bar, beat), 0.42, rev=0.25)
        for s in range(4):
            vel = (0.32, 0.14, 0.6, 0.2)[s]
            add(drums, hat(decay=80 if s != 2 else 35), b(bar, beat + s / 4), vel * 0.35, pan=0.25 if s % 2 else -0.15)
    if bar >= 3:
        add(music, pad(tones, BAR + 0.1, attack=0.25, release=0.3), b(bar), 0.55)
        arp = [tones[i] + 12 for i in (0, 2, 1, 3, 2, 0, 3, 1)]
        for s in range(16):
            m = arp[s % 8] + (12 if s in (6, 14) else 0)
            br = 0.6 + 0.5 * (bar - 3) / 3
            add(music, pluck(m, bright=br, detune=-6), b(bar, s / 4), 0.11, pan=-0.45, rev=0.3)
            add(music, pluck(m, bright=br, detune=6), b(bar, s / 4) + 0.012, 0.11, pan=0.45, rev=0.3)

# Section hits
add(fx, boom(1.0), b(2), 0.45)
add(fx, crash(1.2, 3.5), b(2), 0.12)
add(fx, whoosh(0.34, 500, 8000), b(2, 3.25), 0.3)            # O flies to centre
add(fx, boom(1.2), b(3), 0.5)
for k in range(1, 4):                                          # shape morphs
    add(fx, blip(880 * 2 ** (k * 3 / 12), 0.09, drop=0.3), b(3, k), 0.18, pan=(-0.4, 0.4, 0)[k - 1], rev=0.4)
add(fx, bell(88, 1.0), b(3, 3.5), 0.08, rev=0.6)                 # the fifth colour wakes up
add(fx, whoosh(0.30, 200, 6000, curve=4.0), b(3, 3.36), 0.5)
add(fx, boom(1.8, 90, 30), b(4), 0.85)                         # Skogsgrön reveal
add(fx, crash(2.4, 1.8), b(4), 0.32, rev=0.6)
add(fx, whoosh(0.9, 2000, 9000, curve=1.2) * np.hanning(int(0.9 * SR))[:int(0.9 * SR)], b(4, .7), 0.08)
add(fx, whoosh(0.3, 600, 9000), b(4, 3.36), 0.32)
add(fx, boom(1.2), b(5), 0.5)                                  # cubes
for k, beat in enumerate((1, 2, 3, 3.5)):                      # carousel steps
    add(fx, blip(mtof((76, 79, 83, 86)[k]), 0.09, drop=0.25), b(5, beat), 0.16, pan=(-0.3, 0.3)[k % 2], rev=0.35)
add(fx, whoosh(0.32, 300, 7000), b(5, 3.32), 0.32)
add(fx, boom(1.4, 60, 28), b(6), 0.55)                         # liquid
add(fx, whoosh(0.55, 300, 5000, curve=1.0), b(6), 0.22, pan=-0.2)  # the cable draws itself
for k in range(1, 8):                                          # charge pulses along the cable
    add(fx, blip(mtof(84 + (0, 3, 7, 10)[k % 4]), 0.05, drop=-0.3), b(6, k / 2), 0.07, pan=-0.6 + k * 0.17, rev=0.5)
add(fx, bloop(300), b(6, 2), 0.32, pan=-0.35, rev=0.4)         # products pop in
add(fx, bloop(380), b(6, 2) + 0.08, 0.3, pan=0.35, rev=0.4)
add(fx, whoosh(0.3, 300, 9000, curve=3.5), b(6, 3.36), 0.36)

# Bar 7: montage, eight cuts on eighth notes, snare roll and riser
kick_at(b(7), 1.0)
add(fx, boom(0.8), b(7), 0.4)
add(music, pad(CHORDS['F'][1], BAR - 0.12, attack=0.1, release=0.15), b(7), 0.4)
roll = [k / 2 for k in range(4)] + [2 + k / 4 for k in range(4)] + [3 + k / 8 for k in range(7)]
for k, beat in enumerate(roll):
    add(drums, clap(bright=1200 + 120 * k), b(7, beat), 0.16 + 0.018 * k, rev=0.2)
scale = (69, 72, 76, 79, 81, 84, 88, 91)
for k in range(8):
    add(fx, blip(mtof(scale[k]), 0.06, drop=0.15, square=k % 2 == 1), b(7, k / 2), 0.14, pan=(-0.6, 0.6)[k % 2], rev=0.25)
    kick_at(b(7, k / 2), 0.35, f0=200, decay=14, click=0.8)
rt = tt(BAR - 0.12)
riser = sweep(noise(BAR - 0.12), 'bp', lambda s: 400 * (12000 / 400) ** (s / (BAR - 0.12)), q=0.9)
riser += 0.25 * np.sin(2 * np.pi * np.cumsum(220 * 2 ** (3 * rt / rt[-1])) / SR)
add(fx, riser * (rt / rt[-1]) ** 2.2, b(7), 0.5)

# Bar 8: the logo resolve
T8 = b(8)
kick_at(T8, 1.2, f0=190, decay=4)
add(fx, boom(2.2, 75, 26), T8, 0.95)
add(fx, crash(2.6, 1.3), T8, 0.4, rev=0.7)
add(music, pad((57, 64, 67, 71, 72), 2.4, attack=0.05, release=1.2, warmth=5), T8, 0.7)
add(music, bass(33, 1.9), T8, 0.5)
for k, m in enumerate((81, 84, 88, 91, 93, 96)):
    add(fx, bell(m), T8 + 0.12 + k * BEAT / 2, 0.11, pan=-0.5 + k * 0.2, rev=0.7)
add(fx, bell(100, 2.0), b(8, 3), 0.1, rev=0.8)
add(fx, blip(1760, 0.05, drop=0.0), b(8, 3), 0.12, rev=0.4)
kick_at(b(8, 3), 0.5, f0=120, decay=8)

# ---------- mix ----------
t_all = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    i = int(k * SR)
    seg = t_all[i:] - k
    duck[i:] = np.minimum(duck[i:], 1 - 0.6 * np.exp(-seg / 0.11))
music *= duck

ir_t = tt(2.4)
ir = np.stack([filt(noise(2.4), 'lp', 5000) * np.exp(-ir_t * 2.6) for _ in range(2)])
ir[:, :int(0.012 * SR)] = 0                                    # pre-delay
nfft = 1 << (N + len(ir_t)).bit_length()
S = np.fft.rfft(send, nfft)
wet = np.stack([np.fft.irfft(S * np.fft.rfft(ir[c], nfft), nfft)[:N] for c in range(2)])
wet *= 0.9 / (np.abs(wet).max() + 1e-9) * np.abs(send).max() * 0.6

mix = drums + music + fx + wet
gate = np.ones(N)                                              # breath before the final drop
g0, g1 = int((b(8) - BEAT / 4) * SR), int(b(8) * SR)
gate[g0:g1] = 0.0
gate[g0 - 240:g0] = np.linspace(1, 0, 240)
mix *= gate

# tone: tame the sub (-5 dB shelf under ~90 Hz) and add presence so it translates to laptop and phone speakers
shelf = lambda f: 10 ** (-5 / 20) + (1 - 10 ** (-5 / 20)) * f ** 2 / (f ** 2 + 90 ** 2)
presence = lambda f: 1 + (10 ** (2.5 / 20) - 1) * np.exp(-0.5 * (np.log2(np.maximum(f, 1) / 2800) * 1.6) ** 2)
mix = np.stack([filt(ch, None, 0, resp=lambda f: shelf(f) * presence(f)) for ch in mix])

mix = mix[:, :int(DUR * SR)]
fade = int(0.45 * SR)
mix[:, -fade:] *= np.cos(np.linspace(0, np.pi / 2, fade)) ** 2
mix[:, :240] *= np.linspace(0, 1, 240)
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6)
mix *= 10 ** (-1 / 20) / np.abs(mix).max()

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype('<i2').tobytes())
print('wrote', out, f'{mix.shape[1] / SR:.3f}s')
