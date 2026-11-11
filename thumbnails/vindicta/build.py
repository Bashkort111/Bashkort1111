#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10", "numpy>=1.26"]
# ///
"""Render the Vindicta (Deadlock) YouTube thumbnail, 1280x720.

Everything is vector: a procedural night city under a blood moon (blurred),
a split title in Rubik Wet Paint and the hand-drawn bust from
assets/vindicta.svg. Headless Chrome rasterises the SVG at 2x, Pillow grades
and downsamples it.

    uv run thumbnails/vindicta/build.py
    uv run thumbnails/vindicta/build.py --left СНАЙ --right ПЕР --name sniper
"""
from __future__ import annotations

import argparse
import base64
import math
import os
import random
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
FONT = ASSETS / "fonts" / "RubikWetPaint-Regular.ttf"
W, H = 1280, 720

WARM = ["#ffcf7a", "#ffb35c", "#ffe2a8", "#ff9a4d", "#ffc46b"]
TEAL = "#7fe3ff"


def f(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------- crows ----
def _rot(p, pivot, deg):
    a = math.radians(deg)
    x, y = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + x * math.cos(a) - y * math.sin(a), pivot[1] + x * math.sin(a) + y * math.cos(a))


def crow_path(flap: float = 0.0) -> str:
    """Symmetric flying crow seen from below, head up, ~220 wide. flap>0 raises wings."""
    start = (0.0, -52.0)
    head = [("L", (-3.5, -42)), ("C", (-7, -41), (-9, -36), (-8.5, -31)), ("C", (-8, -27), (-7, -24), (-6.5, -21))]
    wing = [
        ("C", (-24, -27), (-52, -36), (-78, -38)),
        ("C", (-90, -39), (-100, -36), (-108, -31)),
        ("L", (-98, -27)), ("L", (-110, -21)), ("L", (-98, -18)), ("L", (-106, -11)),
        ("L", (-93, -10)), ("L", (-97, -3)), ("L", (-84, -5)),
    ]
    tail = [
        ("C", (-62, -6), (-34, -1), (-9, 6)),
        ("C", (-10, 14), (-9, 22), (-8, 28)),
        ("L", (-17, 44)), ("L", (-9, 46)), ("L", (-4, 49)), ("L", (0, 49)),
    ]
    pivot = (-8.0, -10.0)
    wing = [(s[0], *[_rot(p, pivot, flap) for p in s[1:]]) for s in wing]
    tail[0] = ("C", _rot(tail[0][1], pivot, flap * 0.6), tail[0][2], tail[0][3])
    segs = head + wing + tail

    pts = [start] + [s[-1] for s in segs]
    d = [f"M {f(start[0])} {f(start[1])}"]
    for s in segs:
        d.append(s[0] + " " + ", ".join(f"{f(x)} {f(y)}" for x, y in s[1:]))
    # mirrored right side, walked backwards
    for i in range(len(segs) - 1, -1, -1):
        s, prev = segs[i], pts[i]
        m = lambda p: (-p[0], p[1])  # noqa: E731
        if s[0] == "L":
            d.append(f"L {f(m(prev)[0])} {f(m(prev)[1])}")
        else:
            c1, c2 = m(s[2]), m(s[1])
            d.append(f"C {f(c1[0])} {f(c1[1])}, {f(c2[0])} {f(c2[1])}, {f(m(prev)[0])} {f(m(prev)[1])}")
    return " ".join(d) + " Z"


def crow(x, y, scale, rot, flap, fill="#07060e", extra="") -> str:
    return (f'<path d="{crow_path(flap)}" fill="{fill}" {extra} '
            f'transform="translate({f(x)} {f(y)}) rotate({f(rot)}) scale({scale})"/>')


# ----------------------------------------------------------- background ----
def building(rng, x, w, top, color, win, lit, base=H + 20):
    out = [f'<rect x="{f(x)}" y="{f(top)}" width="{f(w)}" height="{f(base - top)}" fill="{color}"/>']
    ww, wh, gx, gy = win
    cols = int((w - gx) // (ww + gx))
    rows = int((base - top - gy) // (wh + gy))
    x0 = x + (w - cols * (ww + gx) + gx) / 2
    for r in range(rows):
        for c in range(cols):
            if rng.random() < lit:
                col = TEAL if rng.random() < 0.04 else rng.choice(WARM)
                out.append(f'<rect x="{f(x0 + c * (ww + gx))}" y="{f(top + gy + r * (wh + gy))}" '
                           f'width="{ww}" height="{wh}" fill="{col}" opacity="{rng.uniform(.35, .95):.2f}"/>')
    return out


def roof(rng, kind, x, w, top, color):
    if kind == "step":
        h1, h2 = rng.uniform(14, 30), rng.uniform(12, 26)
        return [f'<rect x="{f(x + w * .14)}" y="{f(top - h1)}" width="{f(w * .72)}" height="{f(h1 + 1)}" fill="{color}"/>',
                f'<rect x="{f(x + w * .3)}" y="{f(top - h1 - h2)}" width="{f(w * .4)}" height="{f(h2 + 1)}" fill="{color}"/>',
                f'<rect x="{f(x + w * .49)}" y="{f(top - h1 - h2 - 30)}" width="2" height="31" fill="{color}"/>']
    if kind == "spire":
        h = rng.uniform(40, 90)
        return [f'<polygon points="{f(x + w * .25)},{f(top)} {f(x + w * .5)},{f(top - h)} {f(x + w * .75)},{f(top)}" fill="{color}"/>']
    if kind == "tank":
        cx, s = x + w * rng.uniform(.3, .7), rng.uniform(.8, 1.25)
        tw, th, legs = 30 * s, 26 * s, 14 * s
        y0 = top - legs - th
        return [f'<rect x="{f(cx - tw / 2)}" y="{f(y0)}" width="{f(tw)}" height="{f(th)}" rx="3" fill="{color}"/>',
                f'<polygon points="{f(cx - tw / 2 - 2)},{f(y0 + 1)} {f(cx)},{f(y0 - 14 * s)} {f(cx + tw / 2 + 2)},{f(y0 + 1)}" fill="{color}"/>',
                f'<path d="M {f(cx - tw * .4)} {f(y0 + th)} L {f(cx - tw * .45)} {f(top)} M {f(cx + tw * .4)} {f(y0 + th)} '
                f'L {f(cx + tw * .45)} {f(top)} M {f(cx)} {f(y0 + th)} L {f(cx)} {f(top)}" stroke="{color}" stroke-width="2.5"/>']
    return [f'<rect x="{f(x - 2)}" y="{f(top - 5)}" width="{f(w + 4)}" height="6" fill="{color}"/>']


def skyline(rng, *, top, width, color, win, lit, roofs, x0=-60, x1=W + 60):
    out, x = [], x0
    kinds, weights = zip(*roofs.items())
    while x < x1:
        w, t = rng.uniform(*width), rng.uniform(*top)
        out += building(rng, x, w, t, color, win, lit)
        out += roof(rng, rng.choices(kinds, weights)[0], x, w, t, color)
        x += w + rng.uniform(-8, 3)
    return out


def landmarks(color):
    """Art-deco tower (left) and a gothic double spire (right), Deadlock-city flavoured."""
    c = color
    return [
        # art deco tower with stepped crown and needle
        f'<rect x="96" y="250" width="132" height="500" fill="{c}"/>',
        f'<rect x="112" y="214" width="100" height="40" fill="{c}"/>',
        f'<rect x="128" y="182" width="68" height="36" fill="{c}"/>',
        f'<path d="M 138 184 Q 162 120 186 184 Z" fill="{c}"/>',
        f'<polygon points="158,140 162,64 166,140" fill="{c}"/>',
        # gothic church with two spires
        f'<rect x="1018" y="318" width="150" height="430" fill="{c}"/>',
        f'<rect x="1022" y="250" width="40" height="80" fill="{c}"/>',
        f'<rect x="1124" y="250" width="40" height="80" fill="{c}"/>',
        f'<polygon points="1018,254 1042,150 1066,254" fill="{c}"/>',
        f'<polygon points="1120,254 1144,150 1168,254" fill="{c}"/>',
        f'<polygon points="1062,320 1093,268 1124,320" fill="{c}"/>',
        '<circle cx="1093" cy="350" r="14" fill="#ffb35c" opacity=".55"/>',
    ]


def background(rng) -> str:
    out = ['<rect x="-80" y="-80" width="1440" height="880" fill="url(#sky)"/>']
    for _ in range(110):
        out.append(f'<circle cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(0, 330):.0f}" '
                   f'r="{rng.uniform(.6, 1.7):.1f}" fill="#d6e4ff" opacity="{rng.uniform(.2, .85):.2f}"/>')
    # blood moon
    out += ['<circle cx="640" cy="250" r="430" fill="url(#moonHalo)"/>',
            '<circle cx="640" cy="250" r="228" fill="url(#moon)"/>',
            '<rect x="400" y="10" width="480" height="480" filter="url(#moonTex)" clip-path="url(#moonClip)" opacity=".85"/>',
            '<g fill="#08091c" opacity=".78" filter="url(#b8)">'
            '<ellipse cx="500" cy="356" rx="230" ry="13"/><ellipse cx="790" cy="378" rx="250" ry="11"/>'
            '<ellipse cx="720" cy="150" rx="180" ry="8"/><ellipse cx="540" cy="108" rx="130" ry="6"/>'
            '<ellipse cx="300" cy="300" rx="260" ry="9"/><ellipse cx="1000" cy="250" rx="240" ry="9"/></g>']
    # far city + landmarks
    far = "#1d1533"
    out.append('<g>')
    out += landmarks(far)
    out += skyline(rng, top=(330, 450), width=(40, 105), color=far, win=(2.5, 4, 5, 7), lit=.16,
                   roofs={"flat": 4, "step": 2, "spire": 1, "tank": 1})
    out.append('</g>')
    out.append('<rect x="-80" y="300" width="1440" height="460" fill="url(#haze)"/>')
    # ziplines strung between the lanes
    for (x0, y0, xm, ym, x1, y1) in [(-40, 398, 560, 560, 1320, 372), (-40, 470, 640, 600, 1320, 500)]:
        out.append(f'<path d="M {x0} {y0} Q {xm} {ym} {x1} {y1}" fill="none" stroke="#0a0a18" stroke-width="2.5"/>')
        for i in range(1, 24):
            t = i / 24
            px = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * xm + t * t * x1
            py = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * ym + t * t * y1
            out.append(f'<circle cx="{f(px)}" cy="{f(py)}" r="2.6" fill="#ffd98a"/>')
    # mid city
    mid = "#0d0b1d"
    out += skyline(rng, top=(470, 590), width=(60, 140), color=mid, win=(5, 8, 7, 10), lit=.3,
                   roofs={"flat": 3, "step": 1, "tank": 3, "spire": 1})
    out.append('<rect x="-80" y="420" width="1440" height="340" fill="url(#fog)"/>')
    out.append('<ellipse cx="640" cy="790" rx="900" ry="300" fill="url(#cityGlow)"/>')
    for _ in range(46):
        out.append(f'<circle cx="{rng.uniform(-20, W + 20):.0f}" cy="{rng.uniform(500, 735):.0f}" '
                   f'r="{rng.uniform(3, 13):.1f}" fill="{TEAL if rng.random() < .2 else rng.choice(WARM)}" '
                   f'opacity="{rng.uniform(.18, .5):.2f}"/>')
    # distant crows circling the moon
    for x, y, s, r, fl in [(452, 96, .3, -18, 28), (528, 50, .22, 12, -6), (846, 84, .28, 22, 32),
                           (930, 158, .2, -8, 8), (96, 66, .32, -24, 18), (1184, 54, .26, 18, 26),
                           (1012, 34, .18, 6, 0), (250, 34, .2, -6, 22), (742, 32, .2, 30, 14)]:
        out.append(crow(x, y, s, r, fl, fill="#05040b"))
    return "\n".join(out)


def near_layer() -> str:
    c = "#040309"
    return "\n".join([
        # rooftop water tower, bottom-left
        f'<rect x="58" y="548" width="132" height="96" rx="8" fill="{c}"/>',
        f'<polygon points="50,552 124,488 198,552" fill="{c}"/>',
        f'<path d="M 74 640 L 64 740 M 174 640 L 184 740 M 124 640 L 124 740 M 70 680 L 178 680" stroke="{c}" stroke-width="7"/>',
        # parapet + chimneys, bottom-right
        f'<rect x="-40" y="694" width="1360" height="60" fill="{c}"/>',
        f'<rect x="1150" y="610" width="34" height="120" fill="{c}"/>',
        f'<rect x="1196" y="636" width="26" height="100" fill="{c}"/>',
        f'<rect x="1144" y="602" width="46" height="12" fill="{c}"/>',
    ])


# ---------------------------------------------------------------- title ----
# Title halves sit left/right of the hair silhouette (x 494..786 at text height), condensed horizontally
# because Rubik Wet Paint is wide; the font size is fitted so the wider half spans AVAIL px.
LEFT_END, RIGHT_START, AVAIL, SQUEEZE, TRACK, MAX_SIZE = 494.0, 786.0, 470.0, .74, -6.0, 240.0


def fit_size(left: str, right: str) -> float:
    font = ImageFont.truetype(str(FONT), 100)
    need = max(sum(font.getlength(c) for c in w) / 100 for w in (left, right))
    n = max(len(left), len(right))
    return min(MAX_SIZE, (AVAIL / SQUEEZE - TRACK * (n - 1)) / need)


def title(left: str, right: str, size: float) -> tuple[str, str]:
    """Return (defs, layers) for the split title; left half ends at the hair, right half starts after it."""
    font = ImageFont.truetype(str(FONT), int(size))
    base = 338.0

    def half(word, anchor, align, tilt, rots, dys):
        widths = [font.getlength(ch) for ch in word]
        total = sum(widths) + TRACK * (len(word) - 1)
        x = anchor - total if align == "end" else anchor
        els = []
        for i, ch in enumerate(word):
            cx, y = x + widths[i] / 2, base + dys[i % len(dys)]
            els.append(f'<text x="{f(x)}" y="{f(y)}" transform="rotate({rots[i % len(rots)]} {f(cx)} {f(y - size * .35)})">'
                       f'{escape(ch)}</text>')
            x += widths[i] + TRACK
        return (f'<g transform="rotate({tilt} {f(anchor)} {f(base - size * .35)}) translate({f(anchor)} 0) '
                f'scale({SQUEEZE} 1) translate({f(-anchor)} 0)">{"".join(els)}</g>')

    glyphs = (half(left, LEFT_END, "end", 4, [-4, 2, -2, 3, -1], [0, -7, 5, -3, 4]) +
              half(right, RIGHT_START, "start", -4, [3, -3, 2, -2, 1], [4, -5, 6, -2, 3]))
    defs = f"""
    <g id="tg" font-family="Title" font-size="{f(size)}">{glyphs}</g>
    <linearGradient id="tfill" x1="0" y1="{f(base - size * .78)}" x2="0" y2="{f(base + size * .28)}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffffff"/><stop offset=".42" stop-color="#e2f6ff"/>
      <stop offset=".7" stop-color="#9fd8ff"/><stop offset="1" stop-color="#3a78dc"/>
    </linearGradient>
    <filter id="tglow" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="12"/></filter>"""
    layers = ['<use href="#tg" fill="#58d8ff" stroke="#58d8ff" stroke-width="22" stroke-linejoin="round" filter="url(#tglow)" opacity=".75"/>']
    for i in range(10, 0, -1):
        layers.append(f'<use href="#tg" x="{f(i * .8)}" y="{f(i * 1.4)}" fill="#14061c" stroke="#14061c" stroke-width="16" stroke-linejoin="round"/>')
    layers += ['<use href="#tg" fill="none" stroke="#0a0514" stroke-width="16" stroke-linejoin="round"/>',
               '<use href="#tg" fill="url(#tfill)"/>',
               '<use href="#tg" fill="none" stroke="#ffffff" stroke-width="1.6" opacity=".55" transform="translate(0 -2)"/>']
    return defs, "\n".join(layers)


# ----------------------------------------------------------- foreground ----
FEATHER = ("M 0 0 C 9 -10, 13 -32, 7 -60 L 3 -54 L 5 -68 C 3 -74, 0 -77, -2 -79 C -7 -62, -11 -40, -9 -22 "
           "L -4 -26 L -8 -12 C -6 -7, -3 -3, 0 0 Z")


def foreground(rng) -> str:
    out = []
    for x, y, s, r in [(318, 640, 1.35, -32), (1010, 610, 1.2, 58)]:
        out.append(f'<g transform="translate({x} {y}) rotate({r}) scale({s})">'
                   f'<path d="{FEATHER}" fill="#0b0a14" stroke="#ff6a55" stroke-width=".9" stroke-opacity=".6"/>'
                   f'<path d="M 1 8 L -1 -74" stroke="#34345a" stroke-width="1.3"/>'
                   f'<path d="M -1 -12 L 6 -19 M -2 -26 L 8 -34 M -2 -40 L 8 -49 M -3 -54 L 5 -62 M -2 -18 L -7 -24 '
                   f'M -3 -34 L -9 -41 M -3 -50 L -8 -57" stroke="#22223e" stroke-width=".9"/></g>')
    for _ in range(26):
        x, y = rng.uniform(20, W - 20), rng.uniform(380, 700)
        if 330 < x < 950 and y > 430:
            continue  # keep embers off the body
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(1, 2.4):.1f}" fill="#ff8a55" opacity="{rng.uniform(.5, .95):.2f}" filter="url(#ember)"/>')
    return "\n".join(out)


# ------------------------------------------------------------- assemble ----
DEFS = """
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="720" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#04060f"/><stop offset=".3" stop-color="#0a0f28"/>
  <stop offset=".45" stop-color="#1e1539"/><stop offset=".56" stop-color="#5c1e42"/>
  <stop offset=".68" stop-color="#3c1736"/><stop offset="1" stop-color="#14091b"/>
</linearGradient>
<radialGradient id="moon" cx="600" cy="196" r="270" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#ffb08a"/><stop offset=".4" stop-color="#f0603f"/>
  <stop offset=".76" stop-color="#b8222a"/><stop offset="1" stop-color="#781019"/>
</radialGradient>
<radialGradient id="moonHalo" cx="640" cy="250" r="430" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#ff4b2b" stop-opacity=".6"/><stop offset=".53" stop-color="#ff4b2b" stop-opacity=".45"/>
  <stop offset=".7" stop-color="#d0281e" stop-opacity=".16"/><stop offset="1" stop-color="#a01010" stop-opacity="0"/>
</radialGradient>
<clipPath id="moonClip"><circle cx="640" cy="250" r="228"/></clipPath>
<filter id="moonTex" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency=".012" numOctaves="4" seed="7"/>
  <feColorMatrix type="matrix" values="0 0 0 0 .33  0 0 0 0 .03  0 0 0 0 .05  0 0 0 -2.4 1.45"/>
</filter>
<linearGradient id="haze" x1="0" y1="300" x2="0" y2="760" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#5a2a5a" stop-opacity="0"/><stop offset=".45" stop-color="#5a2a5a" stop-opacity=".2"/>
  <stop offset="1" stop-color="#2a1d45" stop-opacity=".1"/>
</linearGradient>
<linearGradient id="fog" x1="0" y1="420" x2="0" y2="760" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#5a4a86" stop-opacity="0"/><stop offset=".5" stop-color="#5a4a86" stop-opacity=".28"/>
  <stop offset="1" stop-color="#2a1a3a" stop-opacity=".2"/>
</linearGradient>
<radialGradient id="cityGlow" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="#ff7a3c" stop-opacity=".45"/><stop offset="1" stop-color="#ff7a3c" stop-opacity="0"/>
</radialGradient>
<filter id="b8" x="-30%" y="-300%" width="160%" height="700%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="bgBlur" filterUnits="userSpaceOnUse" x="-80" y="-80" width="1440" height="880"><feGaussianBlur stdDeviation="3.2"/></filter>
<filter id="nearBlur" filterUnits="userSpaceOnUse" x="-80" y="-80" width="1440" height="880"><feGaussianBlur stdDeviation="5"/></filter>
<filter id="ember" x="-300%" y="-300%" width="700%" height="700%">
  <feGaussianBlur stdDeviation="2.4" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="charShadow" x="-20%" y="-20%" width="140%" height="140%">
  <feMorphology in="SourceAlpha" operator="dilate" radius="3" result="d"/>
  <feGaussianBlur in="d" stdDeviation="9" result="b"/>
  <feFlood flood-color="#05030d" flood-opacity=".85"/><feComposite in2="b" operator="in" result="s"/>
  <feMerge><feMergeNode in="s"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
"""


def build_html(left: str, right: str, size: float, seed: int) -> str:
    rng = random.Random(seed)
    tdefs, tlayers = title(left, right, size)
    char = (ASSETS / "vindicta.svg").read_text(encoding="utf-8")
    font64 = base64.b64encode(FONT.read_bytes()).decode()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: "Title"; src: url(data:font/ttf;base64,{font64}) format("truetype"); }}
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
svg {{ display: block; }}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>{DEFS}{tdefs}</defs>
<g filter="url(#bgBlur)">{background(rng)}</g>
<g filter="url(#nearBlur)">{near_layer()}</g>
{tlayers}
<g filter="url(#charShadow)">{char}</g>
{foreground(rng)}
</svg></body></html>"""


# --------------------------------------------------------------- render ----
def find_chrome() -> str:
    for name in (os.environ.get("CHROME"), "google-chrome", "chromium", "chromium-browser", "chrome"):
        if name and shutil.which(name):
            return shutil.which(name)
    raise SystemExit("Chrome/Chromium not found; set CHROME=/path/to/chrome")


def render(html: str, scale: int) -> Image.Image:
    with tempfile.TemporaryDirectory() as td:
        page, shot = Path(td) / "thumb.html", Path(td) / "shot.png"
        page.write_text(html, encoding="utf-8")
        cmd = [find_chrome(), "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
               f"--force-device-scale-factor={scale}", f"--window-size={W},{H}",
               "--virtual-time-budget=5000", f"--screenshot={shot}", page.as_uri()]
        subprocess.run(cmd, check=True, capture_output=True, timeout=180)
        img = Image.open(shot).convert("RGB")
        img.load()
    if img.size != (W * scale, H * scale):
        raise SystemExit(f"unexpected screenshot size {img.size}")
    return img.resize((W, H), Image.LANCZOS)


def grade(img: Image.Image, seed: int) -> Image.Image:
    a = np.asarray(img).astype(np.float32) / 255.0
    lum = a @ np.array([.2126, .7152, .0722], dtype=np.float32)
    hi = (a * np.clip((lum - .62) / .38, 0, 1)[..., None] * 255).astype(np.uint8)
    bloom = np.asarray(Image.fromarray(hi).filter(ImageFilter.GaussianBlur(16))).astype(np.float32) / 255.0
    a = 1 - (1 - a) * (1 - bloom * .5)  # screen
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * .46) / (H / 2)) ** 2)
    a *= (1 - .42 * np.clip(d - .62, 0, 1) ** 1.2)[..., None]
    # extra saturation so it holds up next to the channel's very saturated thumbnails
    gray = (a @ np.array([.2126, .7152, .0722], dtype=np.float32))[..., None]
    a = gray + (a - gray) * 1.14
    a += np.random.default_rng(seed).normal(0, .014, (H, W, 1)).astype(np.float32)
    return Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--left", default="ВИНД", help="title half left of the face")
    ap.add_argument("--right", default="ИКТА", help="title half right of the face")
    ap.add_argument("--size", type=float, default=0, help="title font size (0 = fit each half into 480px)")
    ap.add_argument("--seed", type=int, default=13, help="city layout seed")
    ap.add_argument("--scale", type=int, default=2, help="supersampling factor")
    ap.add_argument("--name", default="vindicta_thumbnail", help="output file stem")
    ap.add_argument("--out", type=Path, default=HERE / "out")
    ap.add_argument("--html", action="store_true", help="also keep the composed HTML")
    args = ap.parse_args()

    left, right = args.left.upper(), args.right.upper()
    size = args.size or fit_size(left, right)
    html = build_html(left, right, size, args.seed)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.html:
        (args.out / f"{args.name}.html").write_text(html, encoding="utf-8")
    img = grade(render(html, args.scale), args.seed)
    png, jpg = args.out / f"{args.name}.png", args.out / f"{args.name}.jpg"
    img.save(png, optimize=True)
    img.save(jpg, quality=93, optimize=True, progressive=True)
    print(f"title size {size:.0f}px -> {png} ({png.stat().st_size // 1024} KB), {jpg} ({jpg.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
