#!/usr/bin/env python3
"""The letter constellation: Armenian letters placed in 3D by what a language model learned about them, written as an X3D scene.

Input: either a core-run export (`mashtots-export/1`, from MSH-13; v0 uses its `embeddings.input.cosine36`) or a letters export
(`mashtots-letters/1`, from LTR-7; one similarity matrix per variant: EW, E, W, and their seeds).
Output folder:
    constellation.x3d / constellation.xml   the scene (X3D 4.0, X_ITE 16.5.1; .xml is the same file for the claude.ai viewer)
    constellation.json                      positions, neighbours, scores, grades (what the page and later scenes read)
    glyphs/*.png, halo.png                  one texture per symbol, drawn from Noto Serif Armenian (SIL OFL)
    index.html                              the page (X_ITE from the CDN, its stylesheet inlined; see xite_page())
    xite/                                   X_ITE's helper files, served from the page's own folder

Layout: metric MDS (SMACOF) of the distances 1 - cosine between letters, so near letters in the model are near in the sky; the
page states the layout's stress. When there are two variants (Eastern and Western), the Western layout is rotated onto the Eastern
one (orthogonal Procrustes in 3D) and each letter's star travels between its two places.

usage: python3 -I constellation.py --export core_export.json --out DIR [--variants EW] [--title-note "..."]
"""
from __future__ import annotations

import argparse
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

REPO = HERE.parent.parent
# in the repository the font and X_ITE's helper files live under landing/; in the Colab bundle they travel in letters/assets/
_LAND = REPO / "landing"
_ASSETS = HERE / "assets"
FONT = next((p for p in (_LAND / "fonts" / "notoserifarmenian" / "NotoSerifArmenian[wdth,wght].ttf", _ASSETS / "NotoSerifArmenian.ttf") if p.exists()),
            _ASSETS / "NotoSerifArmenian.ttf")
XITE_LIB = next((p for p in (_LAND / "vendor" / "x_ite" / "assets" / "lib", _ASSETS / "x_ite" / "lib") if p.exists()), _ASSETS / "x_ite" / "lib")
XITE_CSS = next((p for p in (_LAND / "vendor" / "x_ite" / "x_ite.css", _ASSETS / "x_ite" / "x_ite.css") if p.exists()), _ASSETS / "x_ite" / "x_ite.css")
RADIUS = 5.0

# Armenian illumination palette: gold leaf for Mashtots' 36, one pigment per phonetic set, silver for the later two, copper for և
GOLD = (1.00, 0.80, 0.42)
SILVER = (0.78, 0.84, 0.95)
COPPER = (0.96, 0.58, 0.38)
TRIAD_COLOUR = {
    "lips": (0.93, 0.33, 0.24),                 # vermilion
    "back of the tongue": (0.98, 0.66, 0.18),   # saffron
    "teeth": (0.25, 0.80, 0.78),                # turquoise
    "teeth, hissing": (0.92, 0.45, 0.66),       # madder rose
    "palate, hushing": (0.55, 0.82, 0.35),      # verdigris green
}


# ------------------------------------------------------------------------------------------------ similarity -> analysis
def triad_score(cos, symbols, k=2, perms=5000, seed=405):
    """Share of the k nearest neighbours of each set member that are in its own set, and a label-permutation p value."""
    cos = np.asarray(cos, float)
    idx = {c: i for i, c in enumerate(symbols)}
    members = [(idx[c], s) for s in A.TRIADS.values() for c in s if c in idx]

    def score(M):
        hit = 0
        for i, s in members:
            order = [j for j in np.argsort(-M[i]) if j != i][:k]
            hit += sum(symbols[j] in s for j in order)
        return hit / (k * len(members))

    obs = score(cos)
    rng = np.random.default_rng(seed)
    null = np.array([score(cos[np.ix_(p, p)]) for p in (rng.permutation(len(symbols)) for _ in range(perms))])
    return dict(k=k, letters=len(members), within_share=round(obs, 4), chance_mean=round(float(null.mean()), 4),
                p_value=float((1 + (null >= obs).sum()) / (perms + 1)), permutations=perms)


def neighbours(cos, symbols, k=3):
    cos = np.asarray(cos, float)
    out = {}
    for i, c in enumerate(symbols):
        order = [j for j in np.argsort(-cos[i]) if j != i][:k]
        out[c] = [dict(symbol=symbols[j], cosine=round(float(cos[i, j]), 3)) for j in order]
    return out


def smacof(D, dim=3, iters=400, seed=405):
    """Metric MDS by SMACOF, started from classical MDS. Returns positions and Kruskal stress-1."""
    D = np.asarray(D, float)
    n = len(D)
    J = np.eye(n) - 1 / n
    B = -0.5 * J @ (D ** 2) @ J
    w, V = np.linalg.eigh(B)
    order = np.argsort(w)[::-1][:dim]
    X = V[:, order] * np.sqrt(np.maximum(w[order], 1e-9))
    for _ in range(iters):
        dist = np.sqrt(((X[:, None] - X[None]) ** 2).sum(-1)) + np.eye(n)
        Bm = -D / dist
        np.fill_diagonal(Bm, 0)
        np.fill_diagonal(Bm, -Bm.sum(1))
        X = Bm @ X / n
    dist = np.sqrt(((X[:, None] - X[None]) ** 2).sum(-1))
    iu = np.triu_indices(n, 1)
    stress = math.sqrt(((dist[iu] - D[iu]) ** 2).sum() / (D[iu] ** 2).sum())
    return X - X.mean(0), stress


def procrustes(X, Y):
    """Rotate (and reflect) Y onto X, both centred; returns the rotated Y and the per-point residual."""
    U, _, Vt = np.linalg.svd(Y.T @ X)
    Yr = Y @ U @ Vt
    return Yr, np.sqrt(((Yr - X) ** 2).sum(1))


def row_rsa(cos_a, cos_b):
    """Per letter: 1 - Pearson correlation of its similarity row in two models (how much its neighbourhood changed)."""
    a, b = np.asarray(cos_a, float), np.asarray(cos_b, float)
    n = len(a)
    out = []
    for i in range(n):
        m = np.arange(n) != i
        out.append(round(float(1 - np.corrcoef(a[i, m], b[i, m])[0, 1]), 4))
    return out


# ------------------------------------------------------------------------------------------------ inputs
def from_core_export(path):
    """v0: the core run's mashtots-40M input embeddings (36 letters learned; Օ, Ֆ, և placed by hand on an outer ring)."""
    d = json.loads(pathlib.Path(path).read_text())
    inp = d["embeddings"]["input"]
    cos = np.asarray(inp["cosine36"], float)
    return dict(source=f"{inp['source']} input embeddings (core run g4a, {d['built']})", grade=d.get("grade", "Measured"),
                variants={"EW": dict(symbols=list(A.MASHTOTS_36), cosine=cos.tolist(), note="Eastern and Western mixed, 50/50")},
                placed_by_hand=list(A.LATER_2) + [A.LIGATURE])


C_PARAMS = {"tiny": 1, "6M": 6, "15M": 15, "40M": 40, "85M": 85, "150M": 150}


def from_letters_export(path):
    d = json.loads(pathlib.Path(path).read_text())
    assert d.get("schema") == "mashtots-letters/1", d.get("schema")
    lig = next(r["upper"] for r in A.table() if r["group"] == "ligature")      # the table keys the ligature by its parts (ԵՒ)
    fix = lambda syms: [lig if c == A.LIGATURE else c for c in syms]
    # the sky shows one size: the largest that has both dialect-only models (else the largest), first seed only, keyed E / W / EW
    sizes = {}
    for k, v in d["variants"].items():
        pools, _, size = k.partition("@")
        if "_s" not in pools:
            sizes.setdefault(size, {})[pools] = v
    rank = lambda z: (("E" in sizes[z] and "W" in sizes[z]), C_PARAMS.get(z, 0))
    size = max(sizes, key=rank)
    variants = {k: dict(v, symbols=fix(v["symbols"])) for k, v in sizes[size].items()}
    return dict(source=d["source"] + f" (sky: {size})", grade=d["grade"], variants=variants, placed_by_hand=[], size=size,
                extra=d.get("analysis", {}).get(size, {}))


# ------------------------------------------------------------------------------------------------ the layout
def build_layout(inp, order=("E", "W", "EW")):
    variants = [v for v in order if v in inp["variants"]] or list(inp["variants"])
    lay, ref = {}, None
    for v in variants:
        V = inp["variants"][v]
        cos = np.asarray(V["cosine"], float)
        D = np.clip(1 - cos, 0, 2)
        X, stress = smacof(D)
        if ref is None:
            X *= RADIUS / max(1e-9, np.abs(X).max())
            ref = (V["symbols"], X)
            moved = None
        else:
            common = [c for c in V["symbols"] if c in ref[0]]
            ia = [ref[0].index(c) for c in common]
            ib = [V["symbols"].index(c) for c in common]
            Xc = X[ib] - X[ib].mean(0)
            Rc = ref[1][ia] - ref[1][ia].mean(0)
            s = np.linalg.norm(Rc) / max(1e-9, np.linalg.norm(Xc))
            U, _, Vt = np.linalg.svd((Xc * s).T @ Rc)
            X = (X - X[ib].mean(0)) * s @ U @ Vt + ref[1][ia].mean(0)
            moved = dict(zip(common, np.sqrt(((X[ib] - ref[1][ia]) ** 2).sum(1)).round(3).tolist()))
        lay[v] = dict(symbols=V["symbols"], pos=X.round(4).tolist(), stress=round(stress, 3), note=V.get("note", ""),
                      neighbours=neighbours(cos, V["symbols"]), triads=triad_score(cos, V["symbols"]), moved_3d=moved)
    if len(variants) > 1 and "E" in inp["variants"] and "W" in inp["variants"]:
        e, w = inp["variants"]["E"], inp["variants"]["W"]
        common = [c for c in e["symbols"] if c in w["symbols"]]
        ce = np.asarray(e["cosine"])[np.ix_([e["symbols"].index(c) for c in common], [e["symbols"].index(c) for c in common])]
        cw = np.asarray(w["cosine"])[np.ix_([w["symbols"].index(c) for c in common], [w["symbols"].index(c) for c in common])]
        lay["_change"] = dict(symbols=common, rsa=row_rsa(ce, cw))
    return variants, lay


# ------------------------------------------------------------------------------------------------ textures
def draw_glyphs(out, rows):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    g = out / "glyphs"
    g.mkdir(parents=True, exist_ok=True)
    big = ImageFont.truetype(str(FONT), 150)
    small = ImageFont.truetype(str(FONT), 64)
    tiny = ImageFont.truetype(str(FONT), 34)
    for var, f in ((big, None), (small, None), (tiny, None)):
        try:
            var.set_variation_by_axes([100, 500])        # wdth 100, wght 500
        except Exception:                                # the font may load as a static instance
            pass
    names = {}
    for r in rows:
        im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        up = "Եւ" if r["group"] == "ligature" else r["upper"]
        f = big if len(up) == 1 else ImageFont.truetype(str(FONT), 108)
        dr.text((122, 116), up, font=f, fill=(255, 255, 255, 255), anchor="mm")
        dr.text((214, 176), r["lower"], font=small, fill=(255, 255, 255, 235), anchor="mm")
        if r["numeral"]:
            dr.text((128, 228), f"{r['numeral']:,}", font=tiny, fill=(255, 255, 255, 190), anchor="mm")
        glow = im.filter(ImageFilter.GaussianBlur(5))
        base = Image.new("RGBA", im.size, (0, 0, 0, 0))
        base.alpha_composite(Image.eval(glow, lambda v: int(v * 0.6)))
        base.alpha_composite(im)
        fn = f"g{r['index']:02d}.png"
        base.save(g / fn)
        names[r["lower"]] = f"glyphs/{fn}"
    yy, xx = np.mgrid[0:128, 0:128]
    rr = np.sqrt((xx - 63.5) ** 2 + (yy - 63.5) ** 2) / 64
    a = np.clip(1 - rr, 0, 1) ** 2.2
    halo = np.dstack([np.full_like(a, 255), np.full_like(a, 255), np.full_like(a, 255), a * 255]).astype("uint8")
    Image.fromarray(halo, "RGBA").save(out / "halo.png")
    return names


# ------------------------------------------------------------------------------------------------ the scene
def f3(v):
    return " ".join(f"{x:.4g}" for x in v)


def colour_of(r):
    if r["group"] == "later":
        return SILVER
    if r["group"] == "ligature":
        return COPPER
    return TRIAD_COLOUR.get(r["triad"], GOLD)


def write_scene(out, rows, placed, layout, variants, glyph, meta):
    """placed: symbol(upper) -> {variant: [x,y,z]}; one star per symbol, with a PositionInterpolator when it has two places."""
    key_of = {r["upper"]: r for r in rows}
    v0 = variants[0]
    two = len(variants) > 1
    L = []
    w = L.append
    w("<?xml version='1.0' encoding='UTF-8'?>")
    w("<X3D profile='Immersive' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' "
      "xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'>")
    w("<head>")
    for k, v in meta.items():
        w(f"<meta name='{html.escape(k, True)}' content='{html.escape(str(v), True)}'/>")
    w("</head>")
    w("<Scene>")
    w("<WorldInfo title='Letter constellation' info='\"Armenian letters placed by what a language model learned about them\"'/>")
    w("<NavigationInfo type='\"EXAMINE\" \"ANY\"' headlight='false'/>")
    w("<Background skyColor='0.05 0.09 0.22 0.035 0.06 0.15 0.02 0.035 0.09 0.012 0.02 0.055' skyAngle='0.9 1.7 2.6'/>")
    w("<Viewpoint DEF='VP_ALL' description='The whole sky' position='0 1.2 17' orientation='1 0 0 -0.07' fieldOfView='0.7'/>")
    w("<Viewpoint DEF='VP_SIDE' description='From the side' position='17 1 0' orientation='0 1 0 1.5708' fieldOfView='0.7'/>")
    w("<Viewpoint DEF='VP_NEAR' description='Among the letters' position='0 0 7.5' fieldOfView='0.9'/>")
    w("<TimeSensor DEF='SPIN_CLOCK' cycleInterval='180' loop='true'/>")
    w("<OrientationInterpolator DEF='SPIN' key='0 0.25 0.5 0.75 1' keyValue='0 1 0 0 0 1 0 1.5708 0 1 0 3.1416 0 1 0 4.7124 0 1 0 6.2832'/>")
    if two:
        w("<TimeSensor DEF='MORPH_CLOCK' cycleInterval='24' loop='true' enabled='false'/>")
    w("<Transform DEF='SKY'>")
    # the stars
    for r in rows:
        up = r["upper"]
        if up not in placed:
            continue
        p = placed[up]
        c = colour_of(r)
        sid = f"S{r['index']:02d}"
        w(f"<Transform DEF='{sid}' translation='{f3(p[v0])}'>")
        w(f"<MetadataSet containerField='metadata' name='letter'><MetadataString containerField='value' name='symbol' value='\"{up}\" \"{r['lower']}\"'/>"
          f"<MetadataInteger containerField='value' name='index' value='{r['index']}'/>"
          + (f"<MetadataInteger containerField='value' name='numeral' value='{r['numeral']}'/>" if r["numeral"] else "")
          + f"<MetadataString containerField='value' name='group' value='\"{r['group']}\"'/></MetadataSet>")
        w(f"<TouchSensor DEF='T{r['index']:02d}' description='{html.escape(r['name'], True)}'/>")
        w("<Billboard axisOfRotation='0 0 0'>")
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(c)}' transparency='0.55'/><ImageTexture url='\"halo.png\"'/></Appearance>"
          "<IndexedFaceSet solid='false' coordIndex='0 1 2 3 -1'><Coordinate point='-0.9 -0.9 -0.01 0.9 -0.9 -0.01 0.9 0.9 -0.01 -0.9 0.9 -0.01'/>"
          "<TextureCoordinate point='0 0 1 0 1 1 0 1'/></IndexedFaceSet></Shape>")
        tint = (1, 1, 1) if r["group"] == "mashtots" and not r["triad"] else tuple(min(1, 0.45 + 0.6 * x) for x in c)
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(tint)}'/><ImageTexture url='\"{glyph[r['lower']]}\"'/></Appearance>"
          "<IndexedFaceSet solid='false' coordIndex='0 1 2 3 -1'><Coordinate point='-0.55 -0.55 0 0.55 -0.55 0 0.55 0.55 0 -0.55 0.55 0'/>"
          "<TextureCoordinate point='0 0 1 0 1 1 0 1'/></IndexedFaceSet></Shape>")
        w("</Billboard></Transform>")
        if two and len(p) > 1:
            kv = " ".join(f3(p[v]) for v in variants[:2]) + " " + f3(p[variants[0]])
            w(f"<PositionInterpolator DEF='M{r['index']:02d}' key='0 0.5 1' keyValue='{kv}'/>")
    # neighbour threads and the five sets, per variant (only the first is shown in v0)
    lay = layout[v0]
    syms = lay["symbols"]
    pos_of = {s: placed[s][v0] for s in placed}
    pts, cols, idx = [], [], []
    seen = set()
    for s in syms:
        for nb in lay["neighbours"][s][:2]:
            e = tuple(sorted((s, nb["symbol"])))
            if e in seen:
                continue
            seen.add(e)
            same = key_of[s]["triad"] and key_of[s]["triad"] == key_of[nb["symbol"]]["triad"]
            col = TRIAD_COLOUR[key_of[s]["triad"]] if same else (0.55, 0.50, 0.40)
            i0 = len(pts)
            pts += [pos_of[e[0]], pos_of[e[1]]]
            cols += [col, col]
            idx += [i0, i0 + 1, -1]
    w("<Switch DEF='THREADS' whichChoice='0'><Shape><Appearance><UnlitMaterial transparency='0.35'/>"
      "<LineProperties linewidthScaleFactor='1.6'/></Appearance>")
    w(f"<IndexedLineSet colorPerVertex='true' coordIndex='{' '.join(map(str, idx))}'><Coordinate DEF='THREAD_POINTS' point='{' '.join(f3(p) for p in pts)}'/>"
      f"<Color color='{' '.join(f3(c) for c in cols)}'/></IndexedLineSet></Shape></Switch>")
    w("<Switch DEF='SETS' whichChoice='0'><Group>")
    for name, s in A.TRIADS.items():
        if all(c in pos_of for c in s):
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(TRIAD_COLOUR[name])}' transparency='0.8'/></Appearance>"
              f"<TriangleSet solid='false'><Coordinate point='{' '.join(f3(pos_of[c]) for c in s)}'/></TriangleSet></Shape>")
    w("</Group></Switch>")
    # the ligature's two parts
    if "ԵՒ" in placed and "Ե" in pos_of and "Ւ" in pos_of:
        q = placed["ԵՒ"][v0]
        w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(COPPER)}' transparency='0.5'/></Appearance>"
          f"<IndexedLineSet coordIndex='0 1 -1 0 2 -1'><Coordinate point='{f3(q)} {f3(pos_of['Ե'])} {f3(pos_of['Ւ'])}'/></IndexedLineSet></Shape>")
    w("</Transform>")
    w("<ROUTE fromNode='SPIN_CLOCK' fromField='fraction_changed' toNode='SPIN' toField='set_fraction'/>")
    w("<ROUTE fromNode='SPIN' fromField='value_changed' toNode='SKY' toField='set_rotation'/>")
    if two:
        for r in rows:
            if r["upper"] in placed and len(placed[r["upper"]]) > 1:
                w(f"<ROUTE fromNode='MORPH_CLOCK' fromField='fraction_changed' toNode='M{r['index']:02d}' toField='set_fraction'/>")
                w(f"<ROUTE fromNode='M{r['index']:02d}' fromField='value_changed' toNode='S{r['index']:02d}' toField='set_translation'/>")
    w("</Scene>")
    w("</X3D>")
    text = "\n".join(L) + "\n"
    (out / "constellation.x3d").write_text(text, encoding="utf-8")
    (out / "constellation.xml").write_text(text, encoding="utf-8")
    return text


# ------------------------------------------------------------------------------------------------ main
def build(export, out, page=True):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    d = json.loads(pathlib.Path(export).read_text())
    inp = from_letters_export(export) if d.get("schema") == "mashtots-letters/1" else from_core_export(export)
    rows = A.table()
    variants, layout = build_layout(inp)
    placed = {}
    for v in variants:
        for s, p in zip(layout[v]["symbols"], layout[v]["pos"]):
            placed.setdefault(s, {})[v] = p
    # anything without a learned place goes on the outer ring (v0: Օ, Ֆ, և)
    for c in inp.get("placed_by_hand", []):
        if c in A.LATER_2:
            i = A.LATER_2.index(c)
            a = math.radians(205 + 32 * i)
            p = [RADIUS * 1.5 * math.cos(a), -RADIUS * 0.1, RADIUS * 1.5 * math.sin(a)]
        else:
            pe, pw = np.array(placed["Ե"][variants[0]]), np.array(placed["Ւ"][variants[0]])
            p = ((pe + pw) / 2 + np.array([0, 1.2, 0])).tolist()
        placed["ԵՒ" if c == A.LIGATURE else c] = {v: [round(x, 4) for x in p] for v in variants}
    glyph = draw_glyphs(out, rows)
    meta = {"title": "Letter constellation", "creator": "hagopjay and Claude", "generator": "x3d.Mashtots poc/letters/constellation.py",
            "source": inp["source"], "grade": inp["grade"], "layout": f"SMACOF MDS of 1 - cosine; stress {layout[variants[0]]['stress']}",
            "font": "Noto Serif Armenian (SIL Open Font License)", "license": "scene: same as the repository; font: OFL"}
    write_scene(out, rows, placed, layout, variants, glyph, meta)
    info = dict(schema="mashtots-constellation/1", source=inp["source"], grade=inp["grade"], variants=variants,
                placed_by_hand=inp.get("placed_by_hand", []), letters=rows,
                positions={k: v for k, v in placed.items()}, layout=layout, extra=inp.get("extra", {}))
    (out / "constellation.json").write_text(json.dumps(info, ensure_ascii=False, indent=1))
    if XITE_LIB.exists():
        shutil.copytree(XITE_LIB, out / "xite", dirs_exist_ok=True)
    if page:
        import constellation_page as P
        P.write_page(out, info, XITE_CSS.read_text() if XITE_CSS.exists() else "")
    t = layout[variants[0]]["triads"]
    print(f"constellation: {len(placed)} symbols in {out}; variants {variants}; stress {layout[variants[0]]['stress']}; "
          f"sets {t['within_share']} vs chance {t['chance_mean']} (p {t['p_value']:.4f})")
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-page", action="store_true")
    a = ap.parse_args()
    build(a.export, a.out, page=not a.no_page)


if __name__ == "__main__":
    main()
