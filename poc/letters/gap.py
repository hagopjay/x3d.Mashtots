#!/usr/bin/env python3
"""The gap-closing piece: two shores of letters, Eastern and Western, as far apart as the model's Western gap.

usage: python3 letters/gap.py --table ladder_table.json --out DIR [--no-page]

Input is mp_letters.py's ladder table (one row per Western-ladder run: megabytes of Western text the model trained on, bpb on the Eastern
and the Western held-out sets). The gap is bpb_W - bpb_E. The scene (X3D 4.0, no Script) holds both shores; the Western shore sails in
rung by rung (TimeSensor -> PositionInterpolator, CoordinateInterpolator for the 39 threads between twin letters). The page adds the curve,
a power-law fit on the rungs, and buttons that set the rung through the SAI. Every number carries the table's grade.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import shutil
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import alphabet as A  # noqa: E402
import constellation as K  # noqa: E402
from constellation_page import _css_for_shadow  # noqa: E402

D0, SPAN = 1.6, 11.0           # scene units: the shores' distance at gap 0, and the extra distance at the largest gap
GOLD, WEST = (0.93, 0.76, 0.42), (0.36, 0.80, 0.78)


def fit_power(mb, gap):
    """gap = a * MB^-b on the rungs with a positive gap (least squares in log-log). Returns a, b and r^2, or None."""
    x = np.asarray(mb, float)
    y = np.asarray(gap, float)
    m = (x > 0) & (y > 0)
    if m.sum() < 3:
        return None
    lx, ly = np.log(x[m]), np.log(y[m])
    b, la = np.polyfit(lx, ly, 1)
    pred = la + b * lx
    r2 = 1 - ((ly - pred) ** 2).sum() / max(1e-12, ((ly - ly.mean()) ** 2).sum())
    return dict(a=float(math.exp(la)), b=float(-b), r2=float(r2), n=int(m.sum()))


def load(table):
    d = json.loads(pathlib.Path(table).read_text())
    rows = [r for r in d["rows"] if r.get("gap") is not None and r.get("w_mb") is not None]
    sizes = {}
    for r in rows:
        sizes.setdefault(r["size"], []).append(r)
    for s in sizes.values():
        s.sort(key=lambda r: r["w_mb"])
    curves = {}
    for size, rs in sizes.items():
        f = fit_power([r["w_mb"] for r in rs], [r["gap"] for r in rs])
        if f and f["b"] > 0:
            f["mb_to_halve"] = round(rs[-1]["w_mb"] * 2 ** (1 / f["b"]), 1)    # the Western MB at which the fit halves the last rung's gap
        curves[size] = dict(rows=rs, fit=f, monotone=all(b["gap"] < a["gap"] for a, b in zip(rs, rs[1:])))
    rank = lambda z: (len(curves[z]["rows"]), K.C_PARAMS.get(z, 0))
    scene_size = max(curves, key=rank) if curves else None
    return dict(grade=d.get("grade", "Measured"), curves=curves, scene_size=scene_size)


def shore(rows, x, sign):
    """39 letters as a terraced coastline: three rows of 13 in alphabet order, receding from the viewer, each row a step back from the sea."""
    pts = []
    for i in range(len(rows)):
        col, row = i % 13, i // 13
        pts.append((x - sign * 0.55 * row, 0.15 + 1.35 * row, 9.0 - 1.5 * col))
    return pts


def write_scene(out, info, glyph):
    rows = A.table()
    rs = info["curves"][info["scene_size"]]["rows"]
    gmax = max(abs(r["gap"]) for r in rs) or 1.0
    dist = [D0 + SPAN * max(0.0, r["gap"]) / gmax for r in rs]
    east = shore(rows, -D0 / 2, -1)
    west0 = shore(rows, 0.0, 1)                    # the Western shore in its own frame; the Transform puts it at x = dist - D0/2
    f3 = K.f3
    n = len(rs)
    keys = [i / max(1, n - 1) for i in range(n)]
    L = []
    w = L.append
    w("<?xml version='1.0' encoding='UTF-8'?>")
    w("<!DOCTYPE X3D PUBLIC 'ISO//Web3D//DTD X3D 4.0//EN' 'https://www.web3d.org/specifications/x3d-4.0.dtd'>")
    w("<X3D profile='Immersive' version='4.0' xmlns:xsd='http://www.w3.org/2001/XMLSchema-instance' "
      "xsd:noNamespaceSchemaLocation='https://www.web3d.org/specifications/x3d-4.0.xsd'><head>")
    for k, v in (("title", "Two shores"), ("creator", "hagopjay and Claude"), ("generator", "x3d.Mashtots poc/letters/gap.py"),
                 ("description", f"Eastern and Western letters, as far apart as the Western gap (bpb_W - bpb_E) of the {info['scene_size']} ladder"),
                 ("grade", info["grade"]), ("font", "Noto Serif Armenian (SIL Open Font License)")):
        w(f"<meta name='{k}' content='{K.html.escape(str(v), quote=True)}'/>")
    w("</head><Scene>")
    w("<WorldInfo title='Two shores'/>")
    w("<Background skyColor='0.012 0.02 0.05 0.03 0.05 0.11 0.05 0.09 0.17' skyAngle='1.2 1.75'/>")
    w("<NavigationInfo type='\"EXAMINE\" \"ANY\"' headlight='false'/>")
    cx = (dist[0] - D0) / 2
    w(f"<Viewpoint DEF='VP_FRONT' description='Along the sea' position='{cx:.3f} 5.2 19.5' orientation='1 0 0 -0.22' fieldOfView='0.9' "
      f"centerOfRotation='{cx:.3f} 1.5 0'/>")
    w(f"<Viewpoint DEF='VP_ABOVE' description='From above' position='{cx:.3f} 30 0.5' orientation='1 0 0 -1.5708' fieldOfView='0.8' "
      f"centerOfRotation='{cx:.3f} 0 0'/>")
    # the sea: a dark plane with a faint grid of lines, under both shores
    w(f"<Transform translation='{cx:.3f} -0.7 0'><Shape><Appearance><UnlitMaterial emissiveColor='0.03 0.06 0.11' transparency='0.15'/></Appearance>"
      "<Box size='44 0.05 30'/></Shape></Transform>")
    grid = []
    for i in range(-22, 23, 2):
        grid += [(cx + i, -0.66, -14), (cx + i, -0.66, 14)]
    for j in range(-14, 15, 2):
        grid += [(cx - 22, -0.66, j), (cx + 22, -0.66, j)]
    w("<Shape><Appearance><UnlitMaterial emissiveColor='0.10 0.18 0.28' transparency='0.4'/></Appearance>"
      f"<IndexedLineSet coordIndex='{' '.join(f'{2 * i} {2 * i + 1} -1' for i in range(len(grid) // 2))}'>"
      f"<Coordinate point='{' '.join(f3(p) for p in grid)}'/></IndexedLineSet></Shape>")

    def letters(pts, tint, prefix):
        for r, p in zip(rows, pts):
            w(f"<Transform translation='{f3(p)}' scale='0.95 0.95 0.95'><Billboard axisOfRotation='0 0 0'>")
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(tint)}' transparency='0.82'/><ImageTexture url='\"halo.png\"'/></Appearance>"
              "<IndexedFaceSet solid='false' coordIndex='0 1 2 3 -1'><Coordinate point='-1.3 -1.3 0 1.3 -1.3 0 1.3 1.3 0 -1.3 1.3 0'/>"
              "<TextureCoordinate point='0 0 1 0 1 1 0 1'/></IndexedFaceSet></Shape>")
            w(f"<Shape><Appearance><UnlitMaterial emissiveColor='{f3(tint)}'/><ImageTexture url='\"{glyph[r['lower']]}\"'/></Appearance>"
              "<IndexedFaceSet solid='false' coordIndex='0 1 2 3 -1'><Coordinate point='-0.6 -0.6 0 0.6 -0.6 0 0.6 0.6 0 -0.6 0.6 0'/>"
              "<TextureCoordinate point='0 0 1 0 1 1 0 1'/></IndexedFaceSet></Shape></Billboard></Transform>")

    w("<Group DEF='EAST'>")
    letters(east, GOLD, "E")
    w("</Group>")
    w(f"<Transform DEF='WEST' translation='{f3((dist[0] - D0 / 2, 0, 0))}'>")
    letters(west0, WEST, "W")
    w("</Transform>")
    # threads between twin letters: one line per letter, its far end rides with the Western shore
    def thread_points(d):
        return [q for e, ww in zip(east, west0) for q in (e, (ww[0] + d - D0 / 2, ww[1], ww[2]))]
    idx = " ".join(f"{2 * i} {2 * i + 1} -1" for i in range(len(rows)))
    cols = " ".join(f"{f3(GOLD)} {f3(WEST)}" for _ in rows)
    w("<Shape><Appearance><UnlitMaterial transparency='0.55'/></Appearance>"
      f"<IndexedLineSet colorPerVertex='true' coordIndex='{idx}'><Coordinate DEF='BRIDGE' point='{' '.join(f3(p) for p in thread_points(dist[0]))}'/>"
      f"<Color color='{cols}'/></IndexedLineSet></Shape>")
    # the tide: one rung every 4 s, then back to the first
    w(f"<TimeSensor DEF='TIDE' cycleInterval='{4 * n}' loop='true' enabled='true'/>")
    w(f"<PositionInterpolator DEF='WEST_PI' key='{' '.join(f'{k:.4f}' for k in keys)}' "
      f"keyValue='{' '.join(f3((d - D0 / 2, 0, 0)) for d in dist)}'/>")
    w(f"<CoordinateInterpolator DEF='BRIDGE_CI' key='{' '.join(f'{k:.4f}' for k in keys)}' "
      f"keyValue='{' '.join(' '.join(f3(p) for p in thread_points(d)) for d in dist)}'/>")
    w("<ROUTE fromNode='TIDE' fromField='fraction_changed' toNode='WEST_PI' toField='set_fraction'/>")
    w("<ROUTE fromNode='WEST_PI' fromField='value_changed' toNode='WEST' toField='set_translation'/>")
    w("<ROUTE fromNode='TIDE' fromField='fraction_changed' toNode='BRIDGE_CI' toField='set_fraction'/>")
    w("<ROUTE fromNode='BRIDGE_CI' fromField='value_changed' toNode='BRIDGE' toField='set_point'/>")
    w("</Scene></X3D>")
    text = "\n".join(L)
    (out / "gap.x3d").write_text(text, encoding="utf-8")
    (out / "gap.xml").write_text(text, encoding="utf-8")
    return dict(dist=dist, east=east, west0=west0)


PAGE = r"""<title>Two Shores</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Armenian:wght@400;600&family=Spectral:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script>
(() => {
  const CDN = "https://cdn.jsdelivr.net/npm/x_ite@16.5.1/dist/assets/lib/";
  const real = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const u = typeof input === "string" ? input : (input && input.url) || String(input);
    return u.startsWith(CDN) ? real("xite/" + u.slice(CDN.length), init) : real(input, init);
  };
})();
</script>
<script src="https://cdn.jsdelivr.net/npm/x_ite@16.5.1/dist/x_ite.min.js"></script>
<script type="text/x-css" id="xite-css">__XITE_CSS__</script>
<style>
:root { color-scheme: dark; --bg: #070d1c; --panel: #0d1730; --ink: #ebe4d3; --ink-2: #a8a394; --rule: #24304d; --gold: #eec26b; --west: #5ccbc7;
  --f-hy: "Noto Serif Armenian", "Noto Serif", Georgia, serif; --f-text: "Spectral", Georgia, serif; --f-data: "IBM Plex Mono", ui-monospace, monospace; }
body { background: var(--bg); color: var(--ink); font-family: var(--f-text); font-size: 17px; line-height: 1.55; }
.wrap { max-width: 1180px; margin: 0 auto; padding-block: 36px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
h1 { font-weight: 500; font-size: clamp(28px, 4vw, 42px); margin: 0 0 6px; text-wrap: balance; }
.lede { max-width: 64ch; color: var(--ink-2); margin: 0 0 22px; }
.sky { position: relative; aspect-ratio: 16 / 9; max-width: 100%; border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; background: #02050c; }
x3d-canvas { width: 100%; height: 100%; display: block; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0 4px; }
button { font-family: var(--f-data); font-size: 13px; color: var(--ink); background: var(--panel); border: 1px solid var(--rule); border-radius: 4px; padding: 6px 10px; cursor: pointer; }
button[aria-pressed="true"] { border-color: var(--gold); color: var(--gold); }
.status { font-family: var(--f-data); font-size: 12px; color: var(--ink-2); }
.row { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 28px; margin-top: 28px; }
@media (max-width: 820px) { .row { grid-template-columns: 1fr; } }
.chart-wrap { overflow-x: auto; }
svg.chart { width: 100%; min-width: 520px; height: auto; display: block; }
h2 { font-family: var(--f-data); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-2); margin: 0 0 8px; }
.big { font-family: var(--f-data); font-size: 44px; color: var(--west); line-height: 1; }
.big span { font-size: 16px; color: var(--ink-2); }
table { border-collapse: collapse; font-family: var(--f-data); font-size: 12px; width: 100%; }
td, th { padding: 4px 6px; border-bottom: 1px solid var(--rule); text-align: right; }
th:first-child, td:first-child { text-align: left; }
.tbl { overflow-x: auto; }
.grade { font-family: var(--f-data); font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; border: 1px solid var(--rule); border-radius: 3px; padding: 1px 5px; color: var(--ink-2); white-space: nowrap; }
.notes p { font-size: 15px; max-width: 68ch; }
</style>

<div class="wrap">
  <h1>Two Shores</h1>
  <p class="lede">The gold shore is Eastern Armenian; the turquoise shore is Western. The distance between them is how much worse the model reads Western than Eastern. Each step of the tide gives the model more Western text, and the Western shore comes in.</p>
  <div class="sky"><x3d-canvas id="scene" splashScreen="false" notifications="false" contextMenu="false" timings="false" cache="true"></x3d-canvas></div>
  <div class="controls" role="group" aria-label="Scene controls">
    <button type="button" id="b-tide" aria-pressed="true">Tide</button>
    <span id="rungs" class="controls" style="margin:0"></span>
    <button type="button" id="b-above">From above</button>
    <button type="button" id="b-front">Along the sea</button>
  </div>
  <p class="status" id="status">Loading the shores…</p>

  <div class="row">
    <section>
      <h2>The gap as Western text grows</h2>
      <div class="chart-wrap"><svg class="chart" id="chart" role="img" aria-label="Western minus Eastern bits per byte against megabytes of Western text"></svg></div>
    </section>
    <section>
      <h2>What the tide says</h2>
      <div class="big" id="big"></div>
      <p id="said"></p>
      <div class="tbl"><table id="tbl"></table></div>
    </section>
  </div>

  <div class="notes">
    <h2>How it was made</h2>
    <p>Each rung is a model of one size trained on the same Eastern text and a nested share of the Western documents (one eighth, a quarter, half, all of them; the same documents stay in as the share grows). The gap is bits per byte on held-out Western text minus bits per byte on held-out Eastern text. The fit is a straight line in log-log through the rungs with a positive gap, so it is a guide, not a law. <span class="grade" id="g"></span></p>
    <p id="next">The diaspora's own texts would be the next rungs: every contributed book, letter or recording transcript, once its owner consents, moves the Western shore in.</p>
  </div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(() => {
  const $ = (id) => document.getElementById(id);
  const D = JSON.parse($("data").textContent);
  const C = D.curves, S = D.scene_size, R = C[S].rows;
  $("g").textContent = D.grade;
  const mb = (v) => v >= 100 ? v.toFixed(0) : v >= 1 ? v.toFixed(1) : v.toFixed(3);

  // ---------------------------------------------------------------- the curve (log x)
  (function chart() {
    const w = 640, h = 380, pl = 58, pr = 18, pt = 18, pb = 44;
    const all = Object.values(C).flatMap((c) => c.rows);
    const xs = all.map((r) => r.w_mb).filter((v) => v > 0), ys = all.map((r) => r.gap);
    const lx0 = Math.log10(Math.min(...xs)) - 0.15, lx1 = Math.log10(Math.max(...xs)) + 0.15;
    const y0 = Math.min(0, ...ys), y1 = Math.max(...ys) * 1.12 || 1;
    const X = (v) => pl + (Math.log10(v) - lx0) / (lx1 - lx0 || 1) * (w - pl - pr), Y = (v) => h - pb - (v - y0) / (y1 - y0 || 1) * (h - pt - pb);
    let o = `<line x1="${pl}" y1="${Y(0)}" x2="${w - pr}" y2="${Y(0)}" stroke="var(--rule)"/>`;
    for (let e = Math.ceil(lx0); e <= Math.floor(lx1); e++) o += `<line x1="${X(10 ** e)}" y1="${pt}" x2="${X(10 ** e)}" y2="${h - pb}" stroke="var(--rule)" stroke-dasharray="2 4"/><text x="${X(10 ** e)}" y="${h - pb + 18}" fill="var(--ink-2)" font-family="var(--f-data)" font-size="11" text-anchor="middle">${mb(10 ** e)} MB</text>`;
    for (let i = 0; i <= 4; i++) { const v = y0 + (y1 - y0) * i / 4; o += `<text x="${pl - 8}" y="${Y(v) + 4}" fill="var(--ink-2)" font-family="var(--f-data)" font-size="11" text-anchor="end">${v.toFixed(3)}</text>`; }
    o += `<text x="${pl}" y="${h - 6}" fill="var(--ink-2)" font-family="var(--f-data)" font-size="11">Western text the model trained on</text>`;
    o += `<text x="12" y="${pt + 4}" fill="var(--ink-2)" font-family="var(--f-data)" font-size="11" transform="rotate(-90 12 ${pt + 4})" text-anchor="end">gap, bits per byte</text>`;
    const tones = ["var(--west)", "var(--gold)", "#c98bd8", "#e7896d"];
    Object.entries(C).forEach(([size, c], k) => {
      const col = tones[k % tones.length];
      if (c.fit) {
        let d = ""; for (let i = 0; i <= 40; i++) { const lv = lx0 + (lx1 - lx0) * i / 40, v = 10 ** lv; d += `${i ? "L" : "M"}${X(v).toFixed(1)},${Y(c.fit.a * v ** -c.fit.b).toFixed(1)}`; }
        o += `<path d="${d}" fill="none" stroke="${col}" stroke-width="1" stroke-dasharray="5 4" opacity="0.6"/>`;
      }
      o += `<polyline fill="none" stroke="${col}" stroke-width="2" points="${c.rows.map((r) => `${X(r.w_mb)},${Y(r.gap)}`).join(" ")}"/>`;
      for (const r of c.rows) o += `<circle cx="${X(r.w_mb)}" cy="${Y(r.gap)}" r="4.5" fill="${col}"><title>${r.run}: ${mb(r.w_mb)} MB of Western text, gap ${r.gap.toFixed(4)} bpb</title></circle>`;
      const last = c.rows[c.rows.length - 1];
      o += `<text x="${X(last.w_mb) + 8}" y="${Y(last.gap) - 8}" fill="${col}" font-family="var(--f-data)" font-size="12">${size}</text>`;
    });
    $("chart").setAttribute("viewBox", `0 0 ${w} ${h}`); $("chart").innerHTML = o;
  })();

  // ---------------------------------------------------------------- the reading
  const first = R[0], last = R[R.length - 1], f = C[S].fit;
  const closed = first.gap > 0 ? 1 - last.gap / first.gap : 0;
  $("big").innerHTML = first.gap > 0
    ? `${Math.round(closed * 100)}%<span> of the gap closed, ${mb(first.w_mb)} → ${mb(last.w_mb)} MB (${S})</span>`
    : `no gap<span> at ${mb(first.w_mb)} MB: the model already reads this Western test as well as the Eastern one (${S}), so the shores touch</span>`;
  $("said").innerHTML = `${C[S].monotone ? "The gap fell at every rung." : "The gap did not fall at every rung."} ` +
    (f ? `Fit: gap ≈ ${f.a.toFixed(3)} × MB<sup>−${f.b.toFixed(2)}</sup> (r² ${f.r2.toFixed(2)}, ${f.n} rungs)${f.mb_to_halve ? `; on that line, halving the last gap would take about ${mb(f.mb_to_halve)} MB of Western text` : ""}.` : "Too few positive rungs for a fit.") +
    ` <span class="grade">${D.grade}</span>`;
  $("tbl").innerHTML = `<tr><th>run</th><th>Western MB</th><th>share</th><th>epochs</th><th>gap</th></tr>` +
    Object.values(C).flatMap((c) => c.rows).map((r) => `<tr><td>${r.run}</td><td>${mb(r.w_mb)}</td><td>${r.w_share.toFixed(3)}</td><td>${r.w_epochs}</td><td>${r.gap.toFixed(4)}</td></tr>`).join("");

  // ---------------------------------------------------------------- the live shores
  function dress(canvas) {
    const root = canvas.shadowRoot; if (!root) return false;
    if (!root.__dressed) {
      const css = $("xite-css").textContent;
      try { const sh = new CSSStyleSheet(); sh.replaceSync(css); root.adoptedStyleSheets = [...root.adoptedStyleSheets, sh]; }
      catch (e) { const st = document.createElement("style"); st.textContent = css; root.prepend(st); }
      root.__dressed = true;
    }
    const surf = root.querySelector(".x_ite-private-browser"); if (surf) surf.style.display = ""; return !!surf;
  }
  async function boot() {
    try {
      if (typeof X3D === "undefined") throw new Error("X_ITE did not load");
      const canvas = $("scene"), br = canvas.browser;
      dress(canvas);
      let n = 0; const keep = setInterval(() => { dress(canvas); if (++n > 20) clearInterval(keep); }, 250);
      await br.loadURL(new X3D.MFString("gap.xml"));
      dress(canvas);
      const sc = br.currentScene, node = (k) => sc.getNamedNode(k);
      const tide = node("TIDE"), westT = node("WEST"), bridge = node("BRIDGE");
      const tideBtn = $("b-tide");
      const setTide = (on) => { tide.enabled = on; tideBtn.setAttribute("aria-pressed", String(on)); };
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) setTide(false);
      tideBtn.addEventListener("click", () => setTide(tideBtn.getAttribute("aria-pressed") !== "true"));
      R.forEach((r, i) => {
        const b = document.createElement("button"); b.type = "button"; b.textContent = `${mb(r.w_mb)} MB`;
        b.addEventListener("click", () => {
          setTide(false);
          const d = D.dist[i], x = d - D.d0 / 2;
          westT.translation = new X3D.SFVec3f(x, 0, 0);
          const pts = new X3D.MFVec3f();
          D.east.forEach((e, k) => { const ww = D.west0[k]; pts.push(new X3D.SFVec3f(...e)); pts.push(new X3D.SFVec3f(ww[0] + x, ww[1], ww[2])); });
          bridge.point = pts;
          $("status").textContent = `${r.run}: ${mb(r.w_mb)} MB of Western text, gap ${r.gap.toFixed(4)} bpb (${D.grade}).`;
        });
        $("rungs").appendChild(b);
      });
      $("b-above").addEventListener("click", () => (node("VP_ABOVE").set_bind = true));
      $("b-front").addEventListener("click", () => (node("VP_FRONT").set_bind = true));
      $("status").textContent = "Drag to turn the view. Pick a rung to stop the tide there.";
    } catch (e) {
      $("status").textContent = "The live shores need WebGL 2. The curve below shows the same numbers.";
      console.error(e);
    }
  }
  if (document.readyState === "complete") boot(); else window.addEventListener("load", boot);
})();
</script>
"""


def build(table, out, page=True):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    info = load(table)
    if not info["scene_size"]:
        raise SystemExit("no ladder rows with a gap in " + str(table))
    rows = A.table()
    glyph = K.draw_glyphs(out, rows)
    geo = write_scene(out, info, glyph)
    data = dict(schema="mashtots-gap/1", grade=info["grade"], curves=info["curves"], scene_size=info["scene_size"], d0=D0,
                dist=[round(d, 4) for d in geo["dist"]], east=[[round(x, 4) for x in p] for p in geo["east"]],
                west0=[[round(x, 4) for x in p] for p in geo["west0"]])
    (out / "gap.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    if K.XITE_LIB.exists():
        shutil.copytree(K.XITE_LIB, out / "xite", dirs_exist_ok=True)
    if page:
        css = K.XITE_CSS.read_text() if K.XITE_CSS.exists() else ""
        html_ = PAGE.replace("__XITE_CSS__", _css_for_shadow(css)).replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
        (out / "index.html").write_text(html_, encoding="utf-8")
    for size, c in info["curves"].items():
        f = c["fit"]
        print(f"gap {size}: " + ", ".join(f"{r['w_mb']:g} MB -> {r['gap']:.4f}" for r in c["rows"]) + f"; monotone {c['monotone']}"
              + (f"; fit a {f['a']:.3f} b {f['b']:.3f} r2 {f['r2']:.2f}" if f else ""))
    print(f"two shores: {out} (scene size {info['scene_size']}, {len(info['curves'][info['scene_size']]['rows'])} rungs)")
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-page", action="store_true")
    a = ap.parse_args()
    build(a.table, a.out, page=not a.no_page)


if __name__ == "__main__":
    main()
