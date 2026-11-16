#!/usr/bin/env python3
"""Letter Constellation v1, the galaxy edition: every Armenian letter is a star, a constellation and a galaxy, in its own palette.

usage: python3 letters/galaxy.py --export EXPORT.json[.gz] --out DIR [--no-page] [--tex 768]

Reads the same exports as constellation.py (the core model export, or a mashtots-letters/1 export with Eastern and Western variants) and
uses the same layout (SMACOF MDS of 1 - cosine, Procrustes for the second dialect). What is new is how each letter is drawn:

  STAR          the capital, Noto Serif Armenian at weight 700, with a bold ink outline in the letter's deepest colour and a metal rim
                (gold leaf for Mashtots' 36, silver for the later Օ Ֆ, copper for the ligature և), in a corona with diffraction spikes.
  CONSTELLATION the letter's own outline from the font, simplified (Ramer-Douglas-Peucker) into a few dozen stars joined by lines;
                sharp corners become the brightest stars.
  GALAXY        a point-sprite galaxy around it. Size and star count follow how often the letter occurs in the core model's 400 held-out
                windows (Measured, 38 letters). Arms follow the letter's numeral row (units 2, tens 3, hundreds 4, thousands 5 arms).
                The later arrivals are elliptical galaxies (no numeral, no arms). The ligature is two galaxies merging (ե and ւ).

Every letter has its own five-colour palette, built in OKLCH (perceptually even): the five sound sets keep their pigment families
(vermilion lips, saffron back of the tongue, turquoise teeth, rose hissing, verdigris hushing; voiced, plain and aspirated step through
the family), the other Mashtots letters walk the hue wheel by the golden angle in alphabet order, and the later two are moonlight blues.

The scene is X3D 4.0 (Immersive), no Script; X_ITE 16.5.1 renders it. Background: a nebula sphere (procedural, 3D noise, so it has no
seam) and a far starfield. Outputs galaxy.x3d / galaxy.xml, galaxy.json, textures in tex/, and (with the page) index.html.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import html
import json
import math
import pathlib
import shutil
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import alphabet as A  # noqa: E402
import constellation as K  # noqa: E402

VERSION = "v1"
RADIUS = 13.0                 # layout radius (v0 used 5: the galaxies need room)
STAR_Q = 1.75                 # glyph quad half-width, scene units
HALO_Q = 2.9                  # halo quad half-width (corona, spikes, set ring)
CONST_H = 5.2                 # constellation height: it frames the star, it does not echo it
GAL_R = 2.5                   # galaxy base radius; scaled by 0.72 + 0.62 * sqrt(count / max count)
WGHT = 700                    # bold

# ================================================================================================ colour (OKLCH -> sRGB, gamut-mapped)
def _srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def _oklab_to_lin(L, a, b):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                     -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                     -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])


def oklch(L, C, h):
    """sRGB 0..1 for OKLCH (L 0..1, C, h degrees); chroma is reduced until the colour is inside sRGB."""
    for _ in range(80):
        a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
        lin = _oklab_to_lin(L, a, b)
        if lin.min() >= -1e-4 and lin.max() <= 1 + 1e-4:
            break
        C *= 0.94
    return tuple(float(v) for v in _srgb(lin))


def hexc(rgb):
    return "#" + "".join(f"{int(round(max(0, min(1, v)) * 255)):02x}" for v in rgb)


SET_HUE = {"lips": 25, "back of the tongue": 88, "teeth": 200, "teeth, hissing": 318, "palate, hushing": 148}
METAL = {"mashtots": (0.96, 0.78, 0.40), "later": (0.85, 0.89, 0.97), "ligature": (0.95, 0.60, 0.38)}
METAL_NAME = {"mashtots": "gold leaf", "later": "silver", "ligature": "copper"}
ROLES = ("ink", "body", "bright", "hot", "accent")
# Western Armenian letter names in a plain Latin spelling (the alphabet table's latin column is Eastern); reader check pending
LATIN_WEST = {"Ա": "ayp", "Բ": "pen", "Գ": "kim", "Դ": "ta", "Ե": "yech", "Զ": "za", "Է": "e", "Ը": "ët", "Թ": "to", "Ժ": "zhe",
              "Ի": "ini", "Լ": "lyun", "Խ": "khe", "Ծ": "dza", "Կ": "gen", "Հ": "ho", "Ձ": "tsa", "Ղ": "ghad", "Ճ": "je", "Մ": "men",
              "Յ": "hi", "Ն": "nu", "Շ": "sha", "Ո": "vo", "Չ": "cha", "Պ": "be", "Ջ": "che", "Ռ": "ra", "Ս": "se", "Վ": "vev",
              "Տ": "dyun", "Ր": "re", "Ց": "tso", "Ւ": "hyun", "Փ": "pyur", "Ք": "ke", "Օ": "o", "Ֆ": "fe", "ԵՒ": "yev"}
# the core run's corpus (poc/results/g4a-core/READING.md, run g4a, Measured)
CORPUS = dict(total_gb=4.2, western_gb=0.72, western_share=0.5, tokens=771_000_000, western_epochs=3.1,
              source="poc/results/g4a-core/READING.md and RESULTS.md (run g4a, mashtots-40M)", grade="Measured")


def palettes(rows):
    """One five-colour palette per letter: ink (the bold outline), body, bright, hot (the core) and accent (a split complement, for dust)."""
    hue, chroma, light = {}, {}, {}
    for name, s in A.TRIADS.items():
        for j, c in enumerate(s):                  # table order within the set: hue and lightness both step
            hue[c], chroma[c], light[c] = (SET_HUE[name] + (-10, 0, 10)[j]) % 360, 0.21, (0.60, 0.68, 0.76)[j]
    for j, c in enumerate(A.LATER_2):
        hue[c], chroma[c], light[c] = (228 + 34 * j) % 360, 0.10, 0.74
    lig = next(r["upper"] for r in rows if r["group"] == "ligature")
    hue[lig], chroma[lig], light[lig] = 46, 0.14, 0.68
    # the other Mashtots letters, in alphabet order: each takes the body colour (hue x lightness) furthest, in OKLab,
    # from every body colour already used, so no two letters share a colour even where hues must sit close
    plain = [r for r in rows if r["group"] == "mashtots" and not r["triad"]]
    # lightness counts for a third in the search (additive galaxies hide lightness steps), so hues spread first;
    # yellows and greens are only beautiful light, so they are lifted and their chroma capped
    yellow = lambda h: 55 <= h <= 135
    def lab(L, C, h):
        return np.array([0.05 * L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))])
    for c in list(hue):
        if yellow(hue[c]) and c in sum(map(list, A.TRIADS.values()), []):
            light[c], chroma[c] = max(light[c], 0.78), min(chroma[c], 0.17)
    used = [lab(light[c], chroma[c], hue[c]) for c in hue]
    hd = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)
    fam = [SET_HUE[n] for n in A.TRIADS]                                  # keep 14 degrees clear of each sound-set family's span
    cand = [(h, L, 0.17 if yellow(h) else 0.16) for h in range(0, 360, 2) if all(hd(h, f) >= 24 for f in fam)
            for L in ((0.76, 0.81, 0.86) if yellow(h) else (0.62, 0.68, 0.74))]
    for r in plain:
        h, L, Cc = max(cand, key=lambda q: (min(np.linalg.norm(lab(q[1], q[2], q[0]) - u) for u in used), -q[0]))
        hue[r["upper"]], chroma[r["upper"]], light[r["upper"]] = float(h), Cc, L
        used.append(lab(L, Cc, h))
    out = {}
    for r in rows:
        u, h, C = r["upper"], hue[r["upper"]], chroma[r["upper"]]
        Lb = light[u]
        cols = dict(ink=oklch(0.17, C * 0.55, h), body=oklch(Lb, C, h), bright=oklch(0.82, C * 0.82, h),
                    hot=oklch(0.96, C * 0.22, h), accent=oklch(0.80, C * 0.6, (h + 150 if h < 180 else h - 150) % 360))
        out[u] = dict(hue=round(h, 1), chroma=C, set_ring=hexc(oklch(0.78, 0.20, SET_HUE[r["triad"]])) if r["triad"] else None, metal=METAL[r["group"]], metal_name=METAL_NAME[r["group"]],
                      rgb={k: tuple(round(x, 4) for x in v) for k, v in cols.items()}, hex={k: hexc(v) for k, v in cols.items()})
    return out


# ================================================================================================ the star texture
def _font(px):
    from PIL import ImageFont
    f = ImageFont.truetype(str(K.FONT), px)
    try:
        f.set_variation_by_axes([WGHT, 100])     # axis order in this font: wght, wdth
    except Exception:
        pass
    return f


def _mask(text, px, size, centre, stroke=0):
    from PIL import Image, ImageDraw
    im = Image.new("L", (size, size), 0)
    ImageDraw.Draw(im).text(centre, text, font=_font(px), fill=255, anchor="mm", stroke_width=stroke, stroke_fill=255)
    return np.asarray(im, np.float32) / 255


def _blur(a, r):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, r)


def _over(dst, rgb, alpha):
    """Porter-Duff over, straight alpha, in place. dst: (H, W, 4) float; rgb: (3,) or (H, W, 3); alpha: (H, W)."""
    a = np.clip(alpha, 0, 1)[..., None]
    rgb = np.broadcast_to(np.asarray(rgb, np.float32), dst[..., :3].shape)
    out_a = a + dst[..., 3:4] * (1 - a)
    dst[..., :3] = np.where(out_a > 1e-6, (rgb * a + dst[..., :3] * dst[..., 3:4] * (1 - a)) / np.maximum(out_a, 1e-6), 0)
    dst[..., 3:4] = out_a


def star_texture(r, pal, size=384, layers="all", k=1.0):
    """The letter as a star. layers="all": the composite (page thumbnails); "glyph": rim, ink and fill only, alpha 1 inside the rim
    and 0 outside (the scene's opaque MASK pass); "halo": corona, spikes, set ring and rim glow with a hole where the glyph is (the
    scene's additive pass, on a quad 1/k times wider than the glyph quad, so the spikes reach further)."""
    from PIL import Image
    P = pal["rgb"]
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    x, y = (xx - size / 2) / (size / 2), (yy - size / 2) / (size / 2)
    d = np.sqrt(x * x + y * y)
    img = np.zeros((size, size, 4), np.float32)
    up = "Եւ" if r["group"] == "ligature" else r["upper"]
    px = int(size * k * (0.50 if len(up) > 1 else 0.66))
    c = (size * 0.5, size * 0.5)
    fill = _mask(up, px, size, c)
    ink = _mask(up, px, size, c, stroke=max(3, int(size * k * 0.064)))
    rim = _mask(up, px, size, c, stroke=max(4, int(size * k * 0.088)))
    if layers in ("all", "halo"):
        dp = d / k                                    # distance in glyph-quad units
        soft = 1.0 if layers == "all" else 0.7        # additive in the scene: a lighter corona keeps the galaxy core in colour
        _over(img, P["body"], soft * 0.50 * np.exp(-(dp / 0.62) ** 2) * (d < 1))
        _over(img, P["bright"], soft * 0.55 * np.exp(-(dp / 0.30) ** 2))
        spike = np.exp(-(y / 0.022 / k) ** 2) * np.exp(-np.abs(x) / 0.65) + np.exp(-(x / 0.022 / k) ** 2) * np.exp(-np.abs(y) / 0.65)
        u, v = (x + y) / math.sqrt(2), (x - y) / math.sqrt(2)
        spike += 0.5 * (np.exp(-(v / 0.016 / k) ** 2) * np.exp(-np.abs(u) / 0.30) + np.exp(-(u / 0.016 / k) ** 2) * np.exp(-np.abs(v) / 0.30))
        _over(img, P["hot"], np.clip(spike, 0, 1) * (d < 1))
        if pal.get("set_ring"):                       # sound-set letters wear their family's ring, whatever their own hue
            ring = tuple(int(pal["set_ring"][i:i + 2], 16) / 255 for i in (1, 3, 5))
            _over(img, ring, 0.9 * np.exp(-((dp - 0.90) / (0.018 * (1 if layers == "all" else 1.4))) ** 2))
        _over(img, P["bright"], np.clip(_blur(rim, size * k * 0.06) * 1.9, 0, 1) * 0.95)
        if layers == "halo":
            img[..., 3] *= 1 - np.clip(_blur(rim, 1.0) * 1.2, 0, 1)
    if layers in ("all", "glyph"):
        _over(img, pal["metal"], rim)
        _over(img, P["ink"], ink)
        t = np.clip((yy - size * (0.5 - 0.30 * k)) / (size * 0.55 * k), 0, 1)[..., None]
        grad = (1 - t) * np.asarray(P["hot"]) + t * np.asarray(P["body"])
        _over(img, grad, fill)
        from scipy.ndimage import binary_erosion
        inner = fill - binary_erosion(fill > 0.5, iterations=max(1, size // 160)).astype(np.float32)
        _over(img, P["hot"], np.clip(inner, 0, 1) * 0.55)
    arr = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def sprite_textures(out):
    """Shared point sprites: a soft dot and a four-point spark (white; the per-vertex colour tints them)."""
    from PIL import Image
    n = 64
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    x, y = (xx - n / 2 + 0.5) / (n / 2), (yy - n / 2 + 0.5) / (n / 2)
    d = np.sqrt(x * x + y * y)
    dot = np.exp(-(d / 0.42) ** 2) * (d < 1)
    spark = np.clip(np.exp(-(d / 0.22) ** 2) + 0.9 * (np.exp(-(y / 0.06) ** 2) + np.exp(-(x / 0.06) ** 2)) * np.exp(-d / 0.5), 0, 1) * (d < 1)
    for name, a in (("dot.png", dot), ("spark.png", spark)):
        rgba = np.dstack([np.ones_like(a)] * 3 + [a])
        Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(out / "tex" / name)


def nebula_texture(out, w=4096, seed=405):
    """An equirectangular nebula from 3D value noise sampled on the sphere of directions (so the wrap has no seam)."""
    from PIL import Image
    from scipy.ndimage import map_coordinates
    h = w // 2
    lon = (np.arange(w) + 0.5) / w * 2 * np.pi
    lat = (0.5 - (np.arange(h) + 0.5) / h) * np.pi
    LON, LAT = np.meshgrid(lon, lat)
    dx, dy, dz = np.cos(LAT) * np.sin(LON), np.sin(LAT), np.cos(LAT) * np.cos(LON)
    rng = np.random.default_rng(seed)
    G = 40
    grids = [rng.random((G, G, G)).astype(np.float32) for _ in range(3)]

    def fbm(g, scale, octaves=5, warp=None):
        tot, amp, norm = 0, 1.0, 0
        for o in range(octaves):
            s = scale * 2 ** o
            px, py, pz = dx * s + 7.3 * o, dy * s + 3.1 * o, dz * s + 5.7 * o
            if warp is not None:
                px, py, pz = px + warp * 2.0, py + warp * 1.3, pz - warp * 1.7
            coords = np.stack([px.ravel() % G, py.ravel() % G, pz.ravel() % G])
            tot = tot + amp * map_coordinates(g, coords, order=1, mode="grid-wrap").reshape(dx.shape)
            norm += amp
            amp *= 0.52
        return tot / norm

    warp = fbm(grids[2], 1.6, 3)
    a = fbm(grids[0], 2.2, 6, warp)                 # gas density
    b = fbm(grids[1], 3.0, 5, warp)                 # hue field
    dens = np.clip((a - 0.40) / 0.30, 0, 1) ** 1.6
    band = np.exp(-((0.82 * dy + 0.57 * dx) / 0.42) ** 2)   # a soft Milky-Way-like band, on a diagonal
    dens = np.clip(dens * (0.45 + 0.75 * band), 0, 1)
    deep = np.array([0.012, 0.018, 0.05])
    c1 = np.array(oklch(0.34, 0.12, 292))           # violet
    c2 = np.array(oklch(0.38, 0.09, 215))           # teal
    c3 = np.array(oklch(0.42, 0.11, 350))           # rose dust
    t = np.clip((b - 0.35) / 0.3, 0, 1)[..., None]
    gas = (1 - t) * c1 + t * c2
    gas = gas * (1 - 0.35 * np.clip((a - 0.62) / 0.1, 0, 1)[..., None]) + c3 * 0.35 * np.clip((a - 0.62) / 0.1, 0, 1)[..., None]
    img = deep + gas * dens[..., None] * 0.5
    # dark dust lanes
    lane = np.clip((fbm(grids[1], 5.0, 4) - 0.55) / 0.12, 0, 1)
    img *= (1 - 0.55 * lane * band)[..., None]
    # baked faint stars
    ns = int(9000 * (w / 2048) ** 2)                # stars stay one texel wide as the map grows
    sx, sy = rng.integers(0, w, ns), rng.integers(0, h, ns)
    mag = rng.random(ns) ** 6
    img[sy, sx] = np.maximum(img[sy, sx], (0.18 + 0.6 * mag)[:, None])
    img = np.clip(img, 0, 1)
    Image.fromarray((_srgb(img) * 255).astype(np.uint8)).save(out / "tex" / "nebula.jpg", quality=85, optimize=True, progressive=True)


# ================================================================================================ the constellation: the letter's own outline
def _flatten_glyph(ch):
    from fontTools.pens.basePen import BasePen
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    class Flat(BasePen):
        def __init__(self, gs, steps=6):
            super().__init__(gs)
            self.steps, self.cs, self.cur = steps, [], None

        def _moveTo(self, p):
            self.cur = [p]
            self.cs.append(self.cur)

        def _lineTo(self, p):
            self.cur.append(p)

        def _qCurveToOne(self, c, p):
            a = self.cur[-1]
            for k in range(1, self.steps + 1):
                t = k / self.steps
                u = 1 - t
                self.cur.append((u * u * a[0] + 2 * u * t * c[0] + t * t * p[0], u * u * a[1] + 2 * u * t * c[1] + t * t * p[1]))

        def _curveToOne(self, c1, c2, p):
            a = self.cur[-1]
            for k in range(1, self.steps + 1):
                t = k / self.steps
                u = 1 - t
                self.cur.append(tuple(u ** 3 * a[j] + 3 * u * u * t * c1[j] + 3 * u * t * t * c2[j] + t ** 3 * p[j] for j in (0, 1)))

        def _closePath(self):
            if len(self.cur) > 1 and self.cur[0] == self.cur[-1]:
                self.cur.pop()

        _endPath = _closePath

    if not hasattr(_flatten_glyph, "font"):
        f = TTFont(str(K.FONT))
        _flatten_glyph.font = instancer.instantiateVariableFont(f, {"wght": WGHT, "wdth": 100})
    font = _flatten_glyph.font
    upm, cmap, gs = font["head"].unitsPerEm, font.getBestCmap(), font.getGlyphSet()
    out, x0 = [], 0.0
    for c in ch:
        pen = Flat(gs)
        gs[cmap[ord(c)]].draw(pen)
        out += [[((x / upm) + x0, y / upm) for x, y in cs] for cs in pen.cs if len(cs) >= 3]
        x0 += gs[cmap[ord(c)]].width / upm
    return out


def _rdp(pts, eps):
    pts = np.asarray(pts, float)
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ab = b - a
    n = np.hypot(*ab) or 1e-12
    q = pts - a
    dist = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / n
    i = int(np.argmax(dist))
    if dist[i] > eps:
        return np.vstack([_rdp(pts[: i + 1], eps)[:-1], _rdp(pts[i:], eps)])
    return np.vstack([a, b])


def glyph_constellation(r, eps=0.022):
    """Loops of stars tracing the capital's outline; returns loops (list of (n,2) arrays, height 1, centred) and per-star brightness."""
    ch = "ԵՒ" if r["group"] == "ligature" else r["upper"]
    loops = []
    for c in _flatten_glyph(ch):
        c = np.asarray(c)
        far = int(np.argmax(np.hypot(*(c - c[0]).T)))        # split the closed loop in two halves for RDP
        s = np.vstack([_rdp(c[: far + 1], eps)[:-1], _rdp(np.vstack([c[far:], c[:1]]), eps)[:-1]])
        if len(s) >= 3:
            loops.append(s)
    allp = np.vstack(loops)
    lo, hi = allp.min(0), allp.max(0)
    ctr, hgt = (lo + hi) / 2, max(hi[1] - lo[1], (hi[0] - lo[0]) * 0.8)
    loops = [(lp - ctr) / hgt for lp in loops]
    bright = []
    for lp in loops:
        prev, nxt = np.roll(lp, 1, 0), np.roll(lp, -1, 0)
        v1, v2 = lp - prev, nxt - lp
        ang = np.abs(np.arctan2(v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0], (v1 * v2).sum(1)))
        bright.append(np.clip(ang / 1.6, 0, 1))
    return loops, bright


# ================================================================================================ the galaxy
def numeral_arms(r):
    if r["group"] != "mashtots":
        return 0
    return 2 + r["index"] // 9                              # units 2, tens 3, hundreds 4, thousands 5


def galaxy_points(r, pal, count_norm, seed):
    """Unit-radius galaxy in the XZ plane (Y = thickness). Returns (positions (n,3), rgba (n,4), size class (n,))."""
    rng = np.random.default_rng(seed)
    P = pal["rgb"]
    n = int(700 + 2300 * math.sqrt(count_norm))
    kind = "merger" if r["group"] == "ligature" else ("elliptical" if r["group"] == "later" else "spiral")
    if kind == "spiral":
        arms = numeral_arms(r)
        nb = int(n * 0.16)
        bul = rng.normal(0, 0.13, (nb, 3)) * [1, 0.7, 1]
        t = rng.random(n - nb) ** 0.62
        k = rng.integers(0, arms, n - nb)
        twist = 2.1 + 0.25 * (r["index"] % 4)
        th = 2 * np.pi * k / arms + twist * np.log1p(t * 7) + rng.normal(0, 0.20 + 0.18 * (1 - t), n - nb)
        rad = t + rng.normal(0, 0.035, n - nb)
        disk = np.stack([rad * np.cos(th), rng.normal(0, 0.035 + 0.04 * (1 - t), n - nb), rad * np.sin(th)], 1)
        pos = np.vstack([bul, disk])
        rr = np.concatenate([np.abs(bul).max(1) * 0.8, t])
    elif kind == "elliptical":
        rad = np.clip(rng.exponential(0.30, n), 0, 1.1)
        dirs = rng.normal(0, 1, (n, 3))
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        pos = dirs * rad[:, None] * [1.0, 0.62, 0.78]
        rr = rad
    else:                                                   # two spirals meeting, with a tidal bridge
        parts, rrs = [], []
        for j, (off, rot) in enumerate(((-0.42, 0.0), (0.42, 2.2))):
            m = int(n * 0.44)
            t = rng.random(m) ** 0.65
            k = rng.integers(0, 2, m)
            th = rot + np.pi * k + 2.0 * np.log1p(t * 6) + rng.normal(0, 0.25, m)
            rad = t * 0.62
            p = np.stack([rad * np.cos(th) + off, rng.normal(0, 0.04, m) + (0.06 if j else -0.06), rad * np.sin(th)], 1)
            parts.append(p)
            rrs.append(t)
        m = n - 2 * int(n * 0.44)
        s = rng.random(m)
        bridge = np.stack([-0.42 + 0.84 * s, rng.normal(0, 0.05, m), 0.22 * np.sin(np.pi * s) + rng.normal(0, 0.06, m)], 1)
        parts.append(bridge)
        rrs.append(np.full(m, 0.7))
        pos, rr = np.vstack(parts), np.concatenate(rrs)
    rr = np.clip(rr, 0, 1)
    ramp = [(0.0, P["hot"]), (0.12, P["bright"]), (0.45, P["body"]), (1.0, tuple(0.55 * np.asarray(P["body"])))]
    cols = np.zeros((len(pos), 3))
    for (a0, c0), (a1, c1) in zip(ramp, ramp[1:]):
        m = (rr >= a0) & (rr <= a1)
        f = ((rr[m] - a0) / (a1 - a0))[:, None]
        cols[m] = (1 - f) * np.asarray(c0) + f * np.asarray(c1)
    dust = rng.random(len(pos)) < (0.06 if kind != "elliptical" else 0.03)
    cols[dust] = 0.7 * cols[dust] + 0.3 * np.asarray(P["accent"])
    cols = np.clip(cols * (0.50 + 0.30 * rng.random((len(pos), 1))), 0, 1)       # additive: keep the bulge from clipping flat white
    alpha = np.clip(0.95 - 0.5 * rr + rng.normal(0, 0.06, len(pos)), 0.35, 1)
    size = np.where(rng.random(len(pos)) < 0.05, 2, np.where(rng.random(len(pos)) < 0.25, 1, 0))
    size[rr < 0.05] = 1
    return pos, np.hstack([cols, alpha[:, None]]), size, kind


# ================================================================================================ the scene
def _look_at(eye, target):
    """X3D Viewpoint orientation (axis-angle) for a camera at eye looking at target with +Y up."""
    f = np.asarray(target, float) - np.asarray(eye, float)
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 1, 0])
    r = r / (np.linalg.norm(r) or 1)
    u = np.cross(r, f)
    M = np.array([r, u, -f]).T                              # columns: camera x, y, z in world
    w = math.sqrt(max(0, 1 + M[0, 0] + M[1, 1] + M[2, 2])) / 2
    if w < 1e-6:
        return (0, 1, 0, math.pi)
    x, y, z = (M[2, 1] - M[1, 2]) / (4 * w), (M[0, 2] - M[2, 0]) / (4 * w), (M[1, 0] - M[0, 1]) / (4 * w)
    ang = 2 * math.acos(min(1, w))
    s = math.sqrt(max(1e-12, 1 - w * w))
    return (x / s, y / s, z / s, ang)


def _tilt(seed):
    rng = np.random.default_rng(seed)
    a = rng.uniform(0, 2 * np.pi)
    return (math.cos(a), math.sin(a), 0.0, float(rng.uniform(0.35, 0.75)))   # axis in the billboard's picture plane


def f2(v):
    return " ".join(f"{x:.2f}".rstrip("0").rstrip(".") if abs(x) >= 0.005 else "0" for x in v)


def f3(v):
    return K.f3(v)


def write_scene(out, rows, pal, placed, layout, variants, counts, meta, hand=()):
    hand_set = {"ԵՒ" if c == A.LIGATURE else c for c in hand}
    v0 = variants[0]
    key_of = {r["upper"]: r for r in rows}
    cmax = max(counts.values()) if counts else 1
    cmed = float(np.median(list(counts.values()))) / cmax if counts else 0.25
    L = []
    w = L.append
    w("<?xml version='1.0' encoding='UTF-8'?>")
    w("<!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'>")
    w("<X3D profile='Immersive' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' "
      "xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'><head>")
    for k, v in meta.items():
        w(f"<meta name='{k}' content='{html.escape(str(v), quote=True)}'/>")
    w("<component name='X_ITE' level='1'/>")
    w("</head><Scene>")
    w("<WorldInfo title='Letter Constellation v1: the galaxy edition'/>")
    w("<Background skyColor='0.006 0.01 0.03'/>")
    w("<NavigationInfo DEF='NAV' type='\"EXAMINE\" \"ANY\"' headlight='false' visibilityLimit='0' transitionType='\"LINEAR\"' transitionTime='1.4'/>")
    for k, desc, eye, fov in (("VP_ALL", "The whole sky", (0, 3, 40), 0.72), ("VP_SIDE", "From the side", (40, 4, 0), 0.72),
                              ("VP_NEAR", "Among the letters", (6, 2.5, 16), 0.95)):
        o = _look_at(eye, (0, 0, 0))
        w(f"<Viewpoint DEF='{k}' description='{desc}' position='{f3(eye)}' orientation='{f3(o[:3])} {o[3]:.4f}' fieldOfView='{fov}' centerOfRotation='0 0 0'/>")
    # shared appearances for point sprites (per-vertex colour tints a white sprite)
    ADD = ("<BlendMode sourceColorFactor='SRC_ALPHA' sourceAlphaFactor='ONE' destinationColorFactor='ONE' "
           "destinationAlphaFactor='ONE_MINUS_SRC_ALPHA'/>")
    w("<Transform DEF='NEBULA'><Shape><Appearance><UnlitMaterial emissiveColor='1 1 1'/>"
      "<ImageTexture url='\"tex/nebula.jpg\"'/></Appearance><Sphere radius='420' solid='false'/></Shape></Transform>")
    # far starfield, two sizes
    rng = np.random.default_rng(406)
    for cls, (n, sz) in enumerate(((5200, 1.6), (520, 4.0))):
        d = rng.normal(0, 1, (n, 3))
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        p = d * rng.uniform(170, 260, (n, 1))
        temp = rng.random(n)
        c = np.array([oklch(0.88 + 0.1 * rng.random(), 0.05, 250 if t < 0.55 else (70 if t < 0.85 else 30)) for t in temp])
        w(f"<Shape><Appearance><UnlitMaterial/><ImageTexture url='\"tex/{'dot' if cls == 0 else 'spark'}.png\"'/>"
          f"<PointProperties pointSizeScaleFactor='{sz}' pointSizeMinValue='1' pointSizeMaxValue='{sz * 2}' attenuation='1 0 0'/>{ADD}</Appearance>"
          f"<PointSet><Coordinate point='{' '.join(f2(x) for x in p)}'/><ColorRGBA color='{' '.join(f2((*x, 0.9)) for x in c)}'/></PointSet></Shape>")
    w("<Transform DEF='SKY'>")
    # ---- letters
    # near-constant point size (X_ITE: scale / (1 + 0.055 d), clamped): about 3, 5 and 10 px from the whole sky, 8 to 26 px close up
    gal_pp = {0: (11.5, 2.5, 10), 1: (19, 4, 16), 2: (38, 7, 32)}
    for r in rows:
        up = r["upper"]
        if up not in placed:
            continue
        i, P = r["index"], pal[up]
        p = placed[up][v0]
        cn = counts.get(up)
        cnorm = (cn / cmax) if cn else cmed            # not counted (the ligature): drawn at the median size
        gr = GAL_R * (0.72 + 0.62 * math.sqrt(cnorm))
        ax = _tilt(1000 + i)
        gpos, grgba, gsize, kind = galaxy_points(r, P, cnorm, 2000 + i)
        md = A_meta(r, P, cn, kind, gr)
        w(f"<Transform DEF='S{i:02d}' translation='{f3(p)}'>")
        w("<MetadataSet containerField='metadata' name='letter'>" + "".join(
            f"<MetadataString containerField='value' name='{k}' value='\"{html.escape(str(v), quote=True)}\"'/>" for k, v in md.items()) + "</MetadataSet>")
        # constellation + core star, facing the viewer
        loops, bright = glyph_constellation(r)
        pts = np.vstack(loops) * CONST_H
        br = np.concatenate(bright)
        idx, k0 = [], 0
        for lp in loops:
            n = len(lp)
            idx += [k0 + j for j in range(n)] + [k0, -1]
            k0 += n
        body, hot = P["rgb"]["body"], P["rgb"]["hot"]
        w("<Billboard axisOfRotation='0 0 0'>")
        # galaxy (inside the billboard, so it always opens towards the viewer): tilted disc spinning about its own axis
        w(f"<Switch DEF='GX{i:02d}' whichChoice='0'><Transform rotation='{f3(ax[:3])} {ax[3]:.3f}'><Transform rotation='1 0 0 1.5708' scale='{gr:.3f} {gr:.3f} {gr:.3f}'>"
          f"<Transform DEF='G{i:02d}'>")
        for cls in (0, 1, 2):
            m = gsize == cls
            if not m.any():
                continue
            spr = "spark" if cls == 2 else "dot"
            w(f"<Shape><Appearance><UnlitMaterial/><ImageTexture url='\"tex/{spr}.png\"'/>"
              f"<PointProperties pointSizeScaleFactor='{gal_pp[cls][0]}' pointSizeMinValue='{gal_pp[cls][1]}' pointSizeMaxValue='{gal_pp[cls][2]}' attenuation='1 0.055 0'/>{ADD}</Appearance>"
              f"<PointSet><Coordinate point='{' '.join(f2(x) for x in gpos[m])}'/><ColorRGBA color='{' '.join(f2(x) for x in grgba[m])}'/></PointSet></Shape>")
        w("</Transform></Transform></Transform></Switch>")
        # constellation: the full chart close up; from afar (LOD) only its corner stars, so the bold star leads
        brt = P["rgb"]["bright"]
        ccol = lambda bb, a: [tuple(np.asarray(body) * 0.6 + np.asarray(brt) * 0.4 + (np.asarray(hot) - np.asarray(brt)) * 0.3 * b) + (a,) for b in bb]
        def cpoints(sel, cls, scale, mn, mx, a):
            return (f"<Shape><Appearance><UnlitMaterial/><ImageTexture url='\"tex/{'spark' if cls else 'dot'}.png\"'/>"
                    f"<PointProperties pointSizeScaleFactor='{scale}' pointSizeMinValue='{mn}' pointSizeMaxValue='{mx}' attenuation='1 0.055 0'/>{ADD}</Appearance>"
                    f"<PointSet><Coordinate point='{' '.join(f3((x, y, -0.38)) for x, y in pts[sel])}'/><ColorRGBA color='{' '.join(f2(x) for x in ccol(br[sel], a))}'/></PointSet></Shape>")
        w(f"<Switch DEF='C{i:02d}' whichChoice='0'><LOD range='20'><Group>")
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(tuple(0.5 * np.asarray(body) + 0.5 * np.asarray(brt)))}' transparency='0.3'/><LineProperties linewidthScaleFactor='2.4'/>{ADD}</Appearance>"
          f"<IndexedLineSet coordIndex='{' '.join(map(str, idx))}'><Coordinate DEF='CP{i:02d}' point='{' '.join(f3((x, y, -0.4)) for x, y in pts)}'/></IndexedLineSet></Shape>")
        for cls, sel in ((0, br < 0.45), (1, br >= 0.45)):
            if sel.any():
                w(cpoints(sel, cls, 26 if cls else 16, 3 if cls else 2, 24 if cls else 14, 0.8))
        w("</Group><Group>")
        if (br >= 0.45).any():
            w(cpoints(br >= 0.45, 1, 18, 2.5, 9, 0.8))
        w("</Group></LOD></Switch>")
        f = 1.15 if r["group"] == "ligature" else 1.0
        def quad(q, z):
            return (f"<IndexedFaceSet solid='false' coordIndex='0 1 2 3 -1'><Coordinate point='{-q} {-q} {z} {q} {-q} {z} {q} {q} {z} {-q} {q} {z}'/>"
                    "<TextureCoordinate point='0 0 1 0 1 1 0 1'/></IndexedFaceSet>")
        if up in hand_set:                              # placed by hand: a dashed ring in the metal colour, as on the flat chart
            rr = STAR_Q * 1.35 * f
            ang = np.linspace(0, 2 * np.pi, 49)[:-1]
            ring = [(rr * math.cos(t), rr * math.sin(t), 0.95) for t in ang]
            ci = " ".join(f"{j} {j + 1} -1" for j in range(0, 48, 2))
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(P['metal'])}' transparency='0.3'/><LineProperties linewidthScaleFactor='1.5'/></Appearance>"
              f"<IndexedLineSet coordIndex='{ci}'><Coordinate point='{' '.join(f3(q) for q in ring)}'/></IndexedLineSet></Shape>")
        # the star: an opaque glyph that writes depth, and an additive halo behind it; only the star takes clicks
        w("<Group>")
        w(f"<Shape><Appearance alphaMode='BLEND'><UnlitMaterial emissiveColor='1 1 1'/><ImageTexture url='\"tex/halo{i:02d}.webp\"'/>{ADD}</Appearance>"
          f"{quad(round(HALO_Q * f, 3), 0.98)}</Shape>")
        w(f"<Shape><Appearance alphaMode='MASK' alphaCutoff='0.5'><UnlitMaterial emissiveColor='1 1 1'/><ImageTexture url='\"tex/glyph{i:02d}.webp\"'/></Appearance>"
          f"{quad(round(STAR_Q * f, 3), 1.0)}</Shape>")
        w(f"<TouchSensor DEF='T{i:02d}' description='{html.escape(r['name'])}'/>")
        w("</Group>")
        w("</Billboard>")
        w("</Transform>")
        if len(variants) > 1:
            kv = " ".join(f3(placed[up][v]) for v in variants[:2]) + " " + f3(placed[up][variants[0]])
            w(f"<PositionInterpolator DEF='M{i:02d}' key='0 0.5 1' keyValue='{kv}'/>")
    # ---- threads between nearest neighbours: inside a sound set they glow in the set's colour, the rest is a faint web
    lay = layout[v0]
    pos_of = {s: placed[s][v0] for s in placed}
    tri_of = {c: name for name, st in A.TRIADS.items() for c in st}
    web, sets_e, seen = [], {}, set()
    for s in lay["symbols"]:
        for nb in lay["neighbours"][s][:2]:
            e = tuple(sorted((s, nb["symbol"])))
            if e in seen:
                continue
            seen.add(e)
            t0, t1 = tri_of.get(e[0]), tri_of.get(e[1])
            (sets_e.setdefault(t0, []) if t0 and t0 == t1 else web).append(e)
    w("<Switch DEF='THREADS' whichChoice='0'><Group>")
    if web:
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='0.34 0.42 0.78' transparency='0.55'/>{ADD}</Appearance>"
          f"<LineSet vertexCount='{' '.join(['2'] * len(web))}'><Coordinate point='{' '.join(f3(pos_of[x]) for e in web for x in e)}'/></LineSet></Shape>")
    for name, es in sets_e.items():
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(oklch(0.80, 0.19, SET_HUE[name]))}' transparency='0.05'/>"
          f"<LineProperties linewidthScaleFactor='2.5'/>{ADD}</Appearance>"
          f"<LineSet vertexCount='{' '.join(['2'] * len(es))}'><Coordinate point='{' '.join(f3(pos_of[x]) for e in es for x in e)}'/></LineSet></Shape>")
    w("</Group></Switch>")
    # ---- the five sets as faint veils
    w("<Switch DEF='SETS' whichChoice='0'><Group>")
    for name, s in A.TRIADS.items():
        if all(c in pos_of for c in s):
            c = oklch(0.62, 0.17, SET_HUE[name])
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(c)}' transparency='0.93'/></Appearance>"
              f"<TriangleSet solid='false'><Coordinate point='{' '.join(f3(pos_of[x]) for x in s)}'/></TriangleSet></Shape>")
            loop = [pos_of[x] for x in s] + [pos_of[s[0]]]
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(c)}' transparency='0.55'/></Appearance>"
              f"<LineSet vertexCount='4'><Coordinate point='{' '.join(f3(q) for q in loop)}'/></LineSet></Shape>")
    w("</Group></Switch>")
    # ---- the ligature's parts (not learned closeness): its own switch
    lig = next(r["upper"] for r in rows if r["group"] == "ligature")
    if lig in pos_of:
        q = pos_of[lig]
        cp = pal[lig]["rgb"]["body"]
        w(f"<Switch DEF='LIG_LINKS' whichChoice='0'><Shape><Appearance><UnlitMaterial emissiveColor='{f3(cp)}' transparency='0.6'/></Appearance>"
          f"<LineSet vertexCount='2 2'><Coordinate point='{f3(q)} {f3(pos_of['Ե'])} {f3(q)} {f3(pos_of['Ւ'])}'/></LineSet></Shape></Switch>")
    # ---- a viewpoint beside every letter (inside SKY, so it turns with the sky)
    for r in rows:
        up = r["upper"]
        if up not in placed:
            continue
        p = np.asarray(placed[up][v0], float)
        out_dir = p / (np.linalg.norm(p) or 1)
        eye = p + out_dir * 7.5 + np.array([0, 1.2, 0])
        o = _look_at(eye, p)
        w(f"<Viewpoint DEF='VL{r['index']:02d}' description='{html.escape(r['name'])}' position='{f3(eye)}' orientation='{f3(o[:3])} {o[3]:.4f}' "
          f"fieldOfView='0.8' centerOfRotation='{f3(p)}'/>")
    w("</Transform>")
    # ---- time
    w("<TimeSensor DEF='SPIN_CLOCK' cycleInterval='300' loop='true'/>")
    w("<OrientationInterpolator DEF='SPIN' key='0 0.25 0.5 0.75 1' keyValue='0 1 0 0 0 1 0 1.5708 0 1 0 3.1416 0 1 0 4.7124 0 1 0 6.2832'/>")
    w("<ROUTE fromNode='SPIN_CLOCK' fromField='fraction_changed' toNode='SPIN' toField='set_fraction'/>")
    w("<ROUTE fromNode='SPIN' fromField='value_changed' toNode='SKY' toField='set_rotation'/>")
    for j, T in enumerate((70, 95, 130)):
        w(f"<TimeSensor DEF='GAL_CLOCK{j}' cycleInterval='{T}' loop='true'/>")
        w(f"<OrientationInterpolator DEF='GAL_SPIN{j}' key='0 0.25 0.5 0.75 1' keyValue='0 1 0 0 0 1 0 -1.5708 0 1 0 -3.1416 0 1 0 -4.7124 0 1 0 -6.2832'/>")
        w(f"<ROUTE fromNode='GAL_CLOCK{j}' fromField='fraction_changed' toNode='GAL_SPIN{j}' toField='set_fraction'/>")
    for r in rows:
        if r["upper"] in placed:
            w(f"<ROUTE fromNode='GAL_SPIN{r['index'] % 3}' fromField='value_changed' toNode='G{r['index']:02d}' toField='set_rotation'/>")
    if len(variants) > 1:
        w("<TimeSensor DEF='MORPH_CLOCK' cycleInterval='16' loop='true' enabled='false'/>")
        for r in rows:
            if r["upper"] in placed:
                w(f"<ROUTE fromNode='MORPH_CLOCK' fromField='fraction_changed' toNode='M{r['index']:02d}' toField='set_fraction'/>")
                w(f"<ROUTE fromNode='M{r['index']:02d}' fromField='value_changed' toNode='S{r['index']:02d}' toField='set_translation'/>")
    w("</Scene></X3D>")
    text = "\n".join(L)
    (out / "galaxy.x3d").write_text(text, encoding="utf-8")
    (out / "galaxy.xml").write_text("\n".join(x for x in L if not x.startswith("<!DOCTYPE")), encoding="utf-8")   # served copy: no DTD
    return len(text)


def A_meta(r, P, count, kind, gr):
    return dict(name=r["name"], latin=r["latin"], palette=" ".join(P["hex"][k] for k in ROLES), galaxy=kind,
                arms=numeral_arms(r), occurrences=count if count is not None else "not counted")


# ================================================================================================ build
def _load_json(path):
    p = pathlib.Path(path)
    raw = gzip.open(p, "rt", encoding="utf-8").read() if p.suffix == ".gz" else p.read_text(encoding="utf-8")
    return json.loads(raw)


def letter_counts(d):
    """Occurrences of each letter in the core model's held-out windows (Measured), keyed by capital; None if the export lacks them."""
    try:
        occ = d["embeddings"]["contextual"]["occurrences"]
        chars = [x["ch"] for x in d["letters"]] if len(d["letters"]) == len(occ) else list(A.MASHTOTS_36 + A.LATER_2)[: len(occ)]
        windows = d["letters_model"].get("windows_used", {})
        nw = " and ".join(f"{v} {'Eastern (ArmWeb test)' if k.startswith('E') else 'Western (Wikipedia)'}" for k, v in windows.items())
        return dict(zip(chars, occ)), dict(source=f"{sum(windows.values())} held-out text windows ({nw}), capital and small together; "
                                                  f"the windows the core run probed its {d['embeddings']['contextual']['source']} model on "
                                                  "(letter counts do not depend on the model)",
                                           windows=windows, grade=d.get("grade", "Measured"))
    except Exception:
        return {}, dict(source="no counts in this export", grade="-")


def build(export, out, page=True, tex=768):
    out = pathlib.Path(out)
    (out / "tex").mkdir(parents=True, exist_ok=True)
    d = _load_json(export)
    if pathlib.Path(export).suffix == ".gz":
        tmp = out / "_export.json"
        tmp.write_text(json.dumps(d))
        export = tmp
    inp = K.from_letters_export(export) if d.get("schema") == "mashtots-letters/1" else K.from_core_export(export)
    rows = A.table()
    pal = palettes(rows)
    variants, layout = K.build_layout(inp)
    scale = RADIUS / K.RADIUS
    placed = {}
    for v in variants:
        for s, p in zip(layout[v]["symbols"], layout[v]["pos"]):
            placed.setdefault(s, {})[v] = [round(x * scale, 4) for x in p]
    for c in inp.get("placed_by_hand", []):                  # v0 positions for the three without a learned place, scaled
        key = "ԵՒ" if c == A.LIGATURE else c
        if c in A.LATER_2:
            i = A.LATER_2.index(c)
            a = math.radians(205 + 32 * i)
            p = [RADIUS * 1.45 * math.cos(a), -RADIUS * 0.08, RADIUS * 1.45 * math.sin(a)]
        else:
            pe, pw = np.array(placed["Ե"][variants[0]]), np.array(placed["Ւ"][variants[0]])
            mid = (pe + pw) / 2                          # near its parts, but clear of every learned letter's galaxy
            others = [np.array(placed[k][variants[0]]) for k in placed]
            dirs = [np.array(d) / np.linalg.norm(d) for d in itertools.product((-1, 0, 1), repeat=3) if any(d)]
            cand = [mid + st * dv for st in np.arange(2.6, 9.01, 0.4) for dv in dirs]
            ok = [q for q in cand if min(np.linalg.norm(q - o) for o in others) >= 6.0]
            p = min(ok, key=lambda q: (round(float(np.linalg.norm(q - mid)), 3), -q[1])).tolist() if ok else (mid + [0, 2.6, 0]).tolist()
        placed[key] = {v: [round(x, 4) for x in p] for v in variants}
    cen = np.mean([placed[k][variants[0]] for k in placed], axis=0)       # translation only: distances are unchanged
    placed = {k: {v: [round(float(x - c), 4) for x, c in zip(p, cen)] for v, p in pv.items()} for k, pv in placed.items()}
    counts, count_src = letter_counts(d) if d.get("schema") != "mashtots-letters/1" else ({}, dict(source="-", grade="-"))
    # textures
    sprite_textures(out)
    nebula_texture(out)
    for r in rows:
        P, i = pal[r["upper"]], r["index"]
        star_texture(r, P, 256).save(out / "tex" / f"star{i:02d}.webp", "WEBP", quality=90, method=4)               # page thumbnail
        star_texture(r, P, tex, "glyph").save(out / "tex" / f"glyph{i:02d}.webp", "WEBP", quality=92, method=4)      # scene, opaque
        star_texture(r, P, 256, "halo", STAR_Q / HALO_Q).save(out / "tex" / f"halo{i:02d}.webp", "WEBP", quality=88, method=4)
    meta = {"title": "Letter Constellation v1: the galaxy edition", "creator": "hagopjay and Claude", "generator": "x3d.Mashtots poc/letters/galaxy.py",
            "source": inp["source"], "grade": inp["grade"], "layout": f"SMACOF MDS of 1 - cosine; stress {layout[variants[0]]['stress']}",
            "galaxies": f"size and star count from letter occurrences: {count_src['source']} ({count_src['grade']}); arms = numeral row",
            "palettes": "OKLCH, one five-colour palette per letter", "font": "Noto Serif Armenian weight 700 (SIL Open Font License)",
            "license": "scene: same as the repository; font: OFL"}
    nbytes = write_scene(out, rows, pal, placed, layout, variants, counts, meta, inp.get("placed_by_hand", []))
    info = dict(schema="mashtots-galaxy/1", version=VERSION, source=inp["source"], grade=inp["grade"], variants=variants,
                placed_by_hand=inp.get("placed_by_hand", []), letters=rows, palettes=pal, counts=counts, count_source=count_src,
                arms={r["upper"]: numeral_arms(r) for r in rows}, positions=placed, layout=layout, extra=inp.get("extra", {}))
    by = {r["upper"]: r for r in rows}
    cons = {}
    for r in rows:
        lps, brs = glyph_constellation(r)
        cons[r["upper"]] = dict(loops=[[[round(float(x), 3), round(float(y), 3)] for x, y in lp] for lp in lps],
                                bright=[[round(float(b), 2) for b in br] for br in brs])
    gp, gc, gs, _ = galaxy_points(by["Բ"], pal["Բ"], 0.5, 2000 + by["Բ"]["index"])
    keep = np.random.default_rng(7).choice(len(gp), min(900, len(gp)), replace=False)
    legend = dict(galaxy=[[round(float(gp[k, 0]), 3), round(float(gp[k, 2]), 3), int(gs[k]), hexc(gc[k, :3]), round(float(gc[k, 3]), 2)] for k in keep])
    info.update(constellations=cons, legend=legend, latin_west=LATIN_WEST, corpus=CORPUS)
    (out / "galaxy.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    if (out / "_export.json").exists():
        (out / "_export.json").unlink()
    if K.XITE_LIB.exists():
        shutil.copytree(K.XITE_LIB, out / "xite", dirs_exist_ok=True)
        lt = K.XITE_LIB.parent / "linetype"                  # LineProperties pulls linetypes.png; the sandbox cannot fetch it from the CDN
        if lt.exists():
            shutil.copytree(lt, out / "xite" / "linetype", dirs_exist_ok=True)
    if page:
        import galaxy_page as GP
        GP.write_page(out, info, K.XITE_CSS.read_text() if K.XITE_CSS.exists() else "")
    t = layout[variants[0]]["triads"]
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"galaxy {VERSION}: {len(placed)} letters in {out}; scene {nbytes / 1e6:.2f} MB, folder {total / 1e6:.2f} MB; "
          f"sets {t['within_share']} vs chance {t['chance_mean']} (p {t['p_value']:.4f})")
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-page", action="store_true")
    ap.add_argument("--tex", type=int, default=768)
    a = ap.parse_args()
    build(a.export, a.out, page=not a.no_page, tex=a.tex)


if __name__ == "__main__":
    main()
