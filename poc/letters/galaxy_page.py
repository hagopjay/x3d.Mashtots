#!/usr/bin/env python3
"""The page around Letter Constellation v1 (the galaxy edition): the live sky, the letter card with its palette, the palette gallery,
how to read a letter (star, constellation, galaxy), the finding, the flat chart, sources, and the versions strip.

Called by galaxy.build(). Works in the claude.ai viewer: X_ITE from jsDelivr, its stylesheet inlined into its shadow root, its helper files
served from xite/. One deliberate dark look (a night sky), so there is no light variant.
"""
from __future__ import annotations

import json
import pathlib

from constellation_page import TITLE_HY, _css_for_shadow

VERSIONS = [("v0", "First sky", "https://claude.ai/artifact/CgcduzE3HAPXwcM1MYea9m"), ("v1", "The galaxy edition", None)]

PAGE = r"""<title>Letter Constellation v1</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Armenian:wght@400;700;900&family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Spectral:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script>
(() => {
  const CDN = "https://cdn.jsdelivr.net/npm/x_ite@16.5.1/dist/assets/lib/", LT = "https://cdn.jsdelivr.net/npm/x_ite@16.5.1/dist/assets/linetype/";
  const real = window.fetch.bind(window);
  window.fetch = (input, init) => {
    const u = typeof input === "string" ? input : (input && input.url) || String(input);
    if (u.startsWith(CDN)) return real("xite/" + u.slice(CDN.length), init);
    if (u.startsWith(LT)) return real("xite/linetype/" + u.slice(LT.length), init);
    return real(input, init);
  };
})();
</script>
<script src="https://cdn.jsdelivr.net/npm/x_ite@16.5.1/dist/x_ite.min.js"></script>
<script type="text/x-css" id="xite-css">__XITE_CSS__</script>
<style>
:root {
  color-scheme: dark;
  --void: #03050d; --night: #070b1c; --panel: #0c1229; --panel-2: #111a3a; --rule: #1f2a52;
  --ink: #ece6d6; --ink-2: #a9a59a; --gold: #f3c76a; --silver: #d8e0f2; --copper: #f09a62;
  --f-hy: "Noto Serif Armenian", "Noto Serif", serif; --f-disp: "Cormorant Garamond", "Spectral", Georgia, serif;
  --f-text: "Spectral", "Noto Serif Armenian", Georgia, serif; --f-data: "IBM Plex Mono", "Noto Serif Armenian", ui-monospace, Menlo, monospace;
}
:where([lang="hyw"]) { font-family: var(--f-hy); }
.pairs [lang="hyw"], .notes [lang="hyw"], .anatomy p [lang="hyw"], .finding p [lang="hyw"] { font-weight: 700; font-size: 1.05em; }
body { background: var(--void); color: var(--ink); font-family: var(--f-text); font-size: 17px; line-height: 1.55; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); background: var(--void); z-index: 10; }
.wrap { max-width: 1320px; margin: 0 auto; padding-block: 22px 72px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 30px; }
.wrap > *, .stage > * { min-width: 0; }
.versions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-family: var(--f-data); font-size: 12px; color: var(--ink-2); }
.versions a, .versions span.v { border: 1px solid var(--rule); border-radius: 999px; padding: 3px 10px; color: var(--ink-2); text-decoration: none; }
.versions span.v.now { border-color: var(--gold); color: var(--gold); }
.versions a:hover { color: var(--ink); border-color: var(--ink-2); }
header { display: grid; gap: 4px; }
.hy { font-family: var(--f-hy); font-weight: 700; font-size: clamp(32px, 5.4vw, 64px); line-height: 1.05; margin: 0; text-wrap: balance;
  background: linear-gradient(100deg, #ffe7a6 0%, #f3c76a 30%, #e98b5a 55%, #c79bf0 80%, #8fe0de 100%); -webkit-background-clip: text; background-clip: text; color: transparent;
  -webkit-text-stroke: 1px rgba(10, 8, 20, 0.5); }
h1 { font-family: var(--f-disp); font-weight: 600; font-size: clamp(24px, 3vw, 34px); margin: 0; letter-spacing: 0.01em; }
h1 em { font-style: italic; font-weight: 500; color: var(--ink-2); white-space: nowrap; }
.lede { max-width: 70ch; color: var(--ink-2); margin: 6px 0 0; }
.stage { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 18px; align-items: start; }
@media (max-width: 920px) { .stage { grid-template-columns: minmax(0, 1fr); } }
.sky { position: relative; background: #010208; border: 1px solid var(--rule); border-radius: 8px; overflow: hidden; aspect-ratio: 16 / 10; max-width: 100%;
  box-shadow: 0 0 0 1px rgba(243, 199, 106, 0.08), 0 30px 80px -30px rgba(120, 90, 220, 0.35); }
x3d-canvas { width: 100%; height: 100%; display: block; }
.poster { position: absolute; inset: 0; pointer-events: none; transition: opacity .8s; background: radial-gradient(ellipse at 50% 45%, #1a1640 0%, #04060f 70%); display: grid; place-items: center; }
.poster.gone { opacity: 0; }
.poster img { width: 26%; max-width: 220px; opacity: .9; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
button { font-family: var(--f-data); font-size: 13px; color: var(--ink); background: var(--panel); border: 1px solid var(--rule); border-radius: 4px; padding: 8px 12px; min-height: 40px; cursor: pointer; }
button[aria-pressed="true"] { border-color: var(--gold); color: var(--gold); }
button:focus-visible, .tile:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }
.glabel { font-family: var(--f-data); font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--ink-2); align-self: center; margin-right: 4px; }
button.vp[aria-pressed="true"] { border-color: var(--gold); color: var(--gold); }
.status { font-family: var(--f-data); font-size: 13.5px; color: var(--ink); margin-top: 8px; min-height: 1.4em; }
.card { position: sticky; top: 16px; background: linear-gradient(180deg, var(--panel-2), var(--panel)); border: 1px solid var(--rule); border-radius: 8px; padding: 16px 18px 18px; display: grid; gap: 10px; min-width: 0; overflow: hidden; }
.card .hero { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 12px; align-items: center; }
.card .hero img { width: 120px; height: 120px; display: block; }
.card .name { font-family: var(--f-hy); font-size: 30px; font-weight: 700; line-height: 1.15; }
.card .rule { position: absolute; inset: 0 0 auto; height: 4px; }
.card .step { display: flex; gap: 6px; margin-top: 8px; }
.card .step button { min-height: 44px; min-width: 44px; padding: 4px 12px; font-size: 18px; }
.card svg.cons { width: 100%; height: 110px; display: block; border-radius: 6px; }
.card .latin { font-family: var(--f-data); font-size: 12px; color: var(--ink-2); }
.card dl { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 4px 12px; margin: 0; font-size: 15px; }
.card dt { color: var(--ink-2); font-family: var(--f-data); font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em; padding-top: 4px; }
.card dd { margin: 0; min-width: 0; }
.swatches { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; }
.swatches div { border-radius: 4px; height: 40px; position: relative; box-shadow: inset 0 0 0 1px rgba(255,255,255,.08); }
.swatches small { position: absolute; left: 5px; bottom: 3px; font-family: var(--f-data); font-size: 11px; font-weight: 500; letter-spacing: .02em; }
.swatch-roles { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 4px; font-family: var(--f-data); font-size: 10.5px; color: var(--ink-2); text-transform: uppercase; letter-spacing: .05em; }
.ipa { font-family: var(--f-data); }
.hint { color: var(--ink-2); font-size: 14px; margin: 0; }
.finding { display: grid; grid-template-columns: minmax(200px, 280px) minmax(0, 74ch); column-gap: 40px; row-gap: 18px; align-items: start; justify-content: start; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); padding-block: 22px; }
@media (max-width: 640px) { .finding { grid-template-columns: minmax(0, 1fr); } .big { position: static; } }
.big { font-family: var(--f-data); font-size: clamp(40px, 7vw, 68px); color: var(--gold); line-height: 1; font-variant-numeric: tabular-nums; text-shadow: 0 0 24px rgba(243,199,106,.35); }
.big { position: sticky; top: 24px; }
.big span { display: block; margin-top: 10px; font-size: 0.3em; color: var(--ink-2); text-shadow: none; }
.finding p { margin: 0; max-width: 72ch; }
.sets { display: flex; flex-wrap: wrap; gap: 10px 22px; margin-top: 16px; max-width: 74ch; font-family: var(--f-hy); font-size: 22px; font-weight: 700; }
.sets em { font-family: var(--f-data); font-style: normal; font-weight: 400; font-size: 12px; color: var(--ink-2); margin-left: 4px; }
h2 { font-family: var(--f-disp); font-weight: 600; font-size: clamp(22px, 2.4vw, 30px); margin: 0 0 6px; }
.sub { color: var(--ink-2); margin: 0 0 14px; max-width: 72ch; }
.anatomy { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; }
.anatomy article { background: var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 14px 16px; min-width: 0; }
.anatomy h3 { font-family: var(--f-data); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: .09em; color: var(--gold); margin: 0 0 6px; }
.anatomy p { font-size: 15px; margin: 0 0 6px; }
.anatomy svg { width: 100%; height: auto; aspect-ratio: 200 / 120; max-height: 220px; display: block; margin-bottom: 8px; background: radial-gradient(ellipse at 50% 50%, #0d1430, #070b1c 75%); border-radius: 6px; }
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(132px, 1fr)); gap: 10px; }
.tile { background: radial-gradient(circle at 50% 42%, var(--c-glow) 0%, rgba(0,0,0,0) 62%), var(--panel); border: 1px solid var(--rule); border-radius: 8px; padding: 8px 8px 9px; cursor: pointer; display: grid; gap: 6px; color: var(--ink); text-align: left; font: inherit; min-width: 0; }
.tile:hover { border-color: var(--c-body); }
.tile img { width: 100%; aspect-ratio: 1; display: block; }
.tile .strip { display: grid; grid-template-columns: repeat(5, 1fr); height: 10px; border-radius: 3px; overflow: hidden; }
.tile .lbl { display: flex; justify-content: space-between; gap: 6px; font-family: var(--f-data); font-size: 12px; color: var(--ink-2); }
.tile .lbl b { font-family: var(--f-hy); font-size: 16px; color: var(--ink); font-weight: 700; }
.tile[aria-current="true"] { border-color: var(--c-body); box-shadow: 0 0 0 1px var(--c-body), 0 0 24px -6px var(--c-body); }
.pairs { font-size: 15.5px; color: var(--ink-2); margin: 14px 0 0; max-width: 74ch; }
.pairs + .pairs { margin-top: 8px; }
svg.chart { width: 100%; min-width: 0; max-height: 78vh; height: auto; display: block; }
.notes { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; }
.notes section { min-width: 0; }
.notes h3 { font-family: var(--f-data); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-2); margin: 0 0 8px; }
.notes p, .notes li { font-size: 15px; margin: 0 0 8px; }
.notes ul { padding-left: 18px; margin: 0; }
.grade { font-family: var(--f-data); font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; border: 1px solid var(--rule); border-radius: 3px; padding: 1px 5px; color: var(--ink-2); white-space: nowrap; }
.dialects[hidden] { display: none; }
.moved { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 4px 18px; }
.moved li { display: grid; grid-template-columns: 2.2em 1fr 3.6em; align-items: center; gap: 8px; font-family: var(--f-data); font-size: 12px; cursor: pointer; }
.moved .l { font-family: var(--f-hy); font-size: 18px; font-weight: 700; }
.moved .bar { height: 6px; border-radius: 3px; background: var(--rule); position: relative; overflow: hidden; }
.moved .bar i { position: absolute; inset: 0 auto 0 0; border-radius: 3px; }
@media (prefers-reduced-motion: reduce) { .poster { transition: none; } * { scroll-behavior: auto !important; } }
@media (max-width: 920px) { .card { position: relative; top: 0; } }
@media (max-width: 560px) {
  .sky { aspect-ratio: 4 / 5; }
  .gallery { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .tile { padding: 6px; } .tile .lbl { flex-direction: column; gap: 0; } .tile .lbl span { font-size: 11px; }
  .controls { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; } .controls .glabel { grid-column: 1 / -1; }
  .controls button { font-size: 12px; padding: 6px 9px; min-height: 44px; width: 100%; }
  .versions a, .versions span.v { padding: 7px 12px; }
  .card .hero { grid-template-columns: 96px minmax(0, 1fr); } .card .hero img { width: 96px; height: 96px; }
  .big { font-size: 48px; }
}
</style>

<div class="wrap" lang="en">
  <nav class="versions" id="versions" aria-label="Versions"></nav>
  <header>
    <p class="hy" lang="hyw">__TITLE_HY__</p>
    <h1>Letter Constellation <em>· the galaxy edition</em></h1>
    <p class="lede" id="lede"></p>
  </header>

  <div class="stage">
    <div>
      <div class="sky">
        <x3d-canvas id="scene" contentScale="auto" multisampling="8" splashScreen="false" notifications="false" contextMenu="false" timings="false" cache="true"></x3d-canvas>
        <div class="poster" id="poster" aria-hidden="true"></div>
      </div>
      <div class="controls" role="group" aria-label="Scene controls"><span class="glabel">Show</span>
        <button type="button" id="b-spin" aria-pressed="true">Sky turning</button>
        <button type="button" id="b-gspin" aria-pressed="true">Galaxies turning</button>
        <button type="button" id="b-gal" aria-pressed="true">Galaxies</button>
        <button type="button" id="b-const" aria-pressed="true">Constellations</button>
        <button type="button" id="b-threads" aria-pressed="true">Nearest threads</button>
        <button type="button" id="b-sets" aria-pressed="true">The five sets</button>
        <button type="button" id="b-morph" aria-pressed="false" hidden>Eastern ⇄ Western</button>
      </div>
      <div class="controls" id="vps" role="group" aria-label="Viewpoints"><span class="glabel">Go to</span></div>
      <p class="status" id="status" role="status">Loading the sky…</p>
    </div>
    <aside class="card" id="card" tabindex="-1" aria-labelledby="card-name"></aside>
  </div>

  <div class="finding">
    <div class="big" id="big"></div>
    <div>
      <p id="finding-text"></p>
      <div class="sets" id="sets"></div>
      <p class="pairs" id="pairs"></p>
      <p class="pairs" id="pairs2"></p>
    </div>
  </div>

  <section>
    <h2>How to read a letter</h2>
    <p class="sub">Each letter is drawn three ways at once, from the brightest point outwards.</p>
    <div class="anatomy" id="anatomy"></div>
  </section>

  <section>
    <h2>Thirty-nine palettes</h2>
    <p class="sub">Each sound set owns a band of the colour wheel and wears a coloured ring, stepping darker to lighter through the set in table order (<span lang="hyw">բ պ փ</span>). In Western the first and the last letter of a set sound alike; in Eastern they are voiced, plain and aspirated. The other Mashtots letters take the hues left between the sets, each as far as it can get from the hues already used; yellows and greens are lifted, because they are only beautiful light. The two later arrivals are moonlight, and the ligature is copper. Click a letter to fly to it.</p>
    <div class="gallery" id="gallery"></div>
  </section>

  <section class="dialects" id="dialects" hidden>
    <h2>Eastern and Western skies</h2>
    <p class="sub" id="dia-text"></p>
    <ol class="moved" id="moved"></ol>
  </section>

  <section>
    <h2>The flat chart</h2>
    <p class="sub" id="chart-sub"></p>
    <svg class="chart" id="chart" role="group" aria-label="Flat star chart of the letters, seen from the front"></svg>
  </section>

  <div class="notes">
    <section>
      <h3>Where the numbers come from</h3>
      <ul id="sources"></ul>
    </section>
    <section>
      <h3>What is next</h3>
      <p id="next">A letters-only model, trained once on Eastern and once on Western text, will give every symbol a learned place, including Օ, Ֆ and և. Then the sky moves between the two dialects, galaxies and all.</p>
    </section>
  </div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(() => {
  const $ = (id) => document.getElementById(id);
  const D = JSON.parse($("data").textContent);
  const V0 = D.variants[0], LAY = D.layout[V0], ROWS = D.letters, PAL = D.palettes, LW = D.latin_west || {};
  const BY = Object.fromEntries(ROWS.map((r) => [r.upper, r]));
  const IDX = (up) => String(BY[up].index).padStart(2, "0");
  const ROLES = ["ink", "body", "bright", "hot", "accent"];
  const hand = new Set(D.placed_by_hand.map((c) => c === "և" ? "ԵՒ" : c));
  const SETHUE = Object.fromEntries(Object.entries(D.triads).map(([k, s]) => [k, PAL[s[0]].set_ring]));
  const glyph = (r) => r.group === "ligature" ? "Եւ" : r.upper;
  const small = (r) => r.group === "ligature" ? "և" : r.lower;
  const west = (r) => LW[r.upper] || r.latin;
  const fmt = (n) => Number(n).toLocaleString("en-US");
  const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  const C = D.corpus || {};

  $("lede").innerHTML = `Every Armenian letter is a star, a constellation and a galaxy. A small language model learned from a ${C.total_gb ?? 4} GB pool of Armenian text: ${C.tokens ? Math.round(C.tokens / 1e6) + " million tokens, " : ""}drawn half Eastern and half Western. The Western pool is only ${C.western_gb ?? "–"} GB, so it read the Western text about ${C.western_epochs ? Math.round(C.western_epochs) : 3} times over. It learned a vector for every letter, and letters it treats alike sit close together in this sky. Nobody told it how the letters sound. Each letter wears its own palette.`;

  // ---------------------------------------------------------------- versions
  $("versions").innerHTML = "<span>Versions</span>" + D.versions.map(([v, t, url]) => url
    ? `<a href="${url}" target="_blank" rel="noopener">${v} · ${t}</a>` : `<span class="v now" aria-current="page">${v} · ${t}</span>`).join("");

  // ---------------------------------------------------------------- a constellation as SVG
  function consSVG(up, w, h, pad, col, dot) {
    const L = D.constellations[up]; if (!L) return "";
    const all = L.loops.flat(), xs = all.map((p) => p[0]), ys = all.map((p) => p[1]);
    const minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
    const s = Math.min((w - 2 * pad) / (maxx - minx || 1), (h - 2 * pad) / (maxy - miny || 1));
    const X = (x) => w / 2 + (x - (minx + maxx) / 2) * s, Y = (y) => h / 2 - (y - (miny + maxy) / 2) * s;
    let o = L.loops.map((lp) => `<polygon points="${lp.map(([x, y]) => `${X(x).toFixed(1)},${Y(y).toFixed(1)}`).join(" ")}" fill="none" stroke="${col}" stroke-width="1.4" stroke-linejoin="round" opacity=".75"/>`).join("");
    L.loops.forEach((lp, i) => lp.forEach(([x, y], j) => { const b = L.bright[i][j]; o += `<circle cx="${X(x).toFixed(1)}" cy="${Y(y).toFixed(1)}" r="${(1.6 + 2.6 * b).toFixed(1)}" fill="${dot}"/>`; }));
    return o;
  }

  // ---------------------------------------------------------------- the letter card
  let flyTo = null, current = null;
  function card(up, fly) {
    const r = BY[up], P = PAL[up]; current = up;
    const nb = (LAY.neighbours[up] || []).map((n, j) => `<span${j > 1 ? ` style="opacity:.55" title="third nearest, not in the finding"` : ""}><span lang="hyw" style="font-weight:700;color:${PAL[n.symbol].hex.bright}">${small(BY[n.symbol])}</span> <span class="ipa">${n.cosine.toFixed(2)}</span></span>`).join(" · ");
    const cnt = D.counts[up], arms = D.arms[up];
    const gal = r.group === "ligature" ? "two galaxies merging, ե and ւ" : r.group === "later" ? "elliptical: no numeral, no arms" : `${arms} arms (numeral row: ${["units", "tens", "hundreds", "thousands"][arms - 2]})`;
    const where = r.group === "ligature" ? "Placed by hand between ե and ւ in this version; not counted, so its galaxy is drawn at the median size."
      : hand.has(up) ? `The model has a vector for it, but the export this sky was built from kept only the similarities between Mashtots' 36, so its place is set by hand, apart, as a later arrival. Its galaxy size is measured: ${fmt(D.counts[up] || 0)} times in the sample.` : "";
    $("card").innerHTML = `<div class="rule" style="background:linear-gradient(90deg, ${P.hex.body}, ${P.hex.accent})"></div>
      <div class="hero"><img src="tex/star${IDX(up)}.webp" alt="${r.name} (${glyph(r)}), drawn as a star"><div><div class="name" id="card-name" lang="hyw">${glyph(r)} ${small(r)} · ${r.name}</div>
        <div class="latin">${west(r)} · Eastern ${r.latin} · ${P.metal_name} rim</div>
        <div class="step"><button type="button" data-step="-1" aria-label="Previous letter">‹</button><button type="button" data-step="1" aria-label="Next letter">›</button></div></div></div>
      <div><div class="swatches">${ROLES.map((k) => `<div style="background:${P.hex[k]}"><small style="color:${k === "ink" ? P.hex.hot : P.hex.ink}">${P.hex[k].slice(1)}</small></div>`).join("")}</div>
      <div class="swatch-roles">${ROLES.map((k) => `<span>${k}</span>`).join("")}</div></div>
      <svg class="cons" viewBox="0 0 300 110" role="img" aria-label="The constellation of ${r.name}" style="background:${P.hex.ink}">${consSVG(up, 300, 110, 12, P.hex.bright, P.hex.hot)}</svg>
      <dl>
        ${r.numeral ? `<dt>Numeral</dt><dd class="ipa">${fmt(r.numeral)}</dd>` : ""}
        <dt>Western</dt><dd class="ipa">[${r.ipa_west}]${r.sound_differs ? ` <span class="grade">differs</span>` : ""}</dd>
        <dt>Eastern</dt><dd class="ipa">[${r.ipa_east}]</dd>
        ${r.triad ? `<dt>Set</dt><dd><span style="color:${P.set_ring}">◯</span> ${r.triad}</dd>` : ""}
        <dt>Galaxy</dt><dd>${gal}${cnt ? `; ${fmt(cnt)} times in the sample` : ""}</dd>
        ${nb ? `<dt>Nearest</dt><dd>${nb}</dd>` : ""}
        ${r.reform ? `<dt>Spelling</dt><dd>${r.reform}</dd>` : ""}
      </dl>${where ? `<p class="hint">${where}</p>` : ""}`;
    $("card").style.boxShadow = `inset 0 1px 0 ${P.hex.body}55, 0 0 60px -28px ${P.hex.body}`;
    document.querySelectorAll(".tile").forEach((t) => t.dataset.up === up ? t.setAttribute("aria-current", "true") : t.removeAttribute("aria-current"));
    $("status").textContent = `${glyph(r)} ${r.name}, ${west(r)}. ${P.metal_name} rim.`;
    if (fly && flyTo) flyTo(up);
  }
  const step = (dir) => { const i = ROWS.findIndex((r) => r.upper === current); card(ROWS[(i + dir + ROWS.length) % ROWS.length].upper, true); const b = $("card").querySelector(`[data-step="${dir}"]`); if (b) b.focus(); };
  $("card").addEventListener("click", (e) => { const b = e.target.closest("[data-step]"); if (b) step(+b.dataset.step); });
  $("card").addEventListener("keydown", (e) => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { step(e.key === "ArrowRight" ? 1 : -1); e.preventDefault(); } });

  // ---------------------------------------------------------------- the finding, exactly
  const T = LAY.triads, K2 = 2;
  const slots = T.letters * K2, links = Math.round(T.within_share * slots);
  const beat = Math.max(0, Math.round(T.p_value * (T.permutations + 1)) - 1);
  $("big").innerHTML = `${Math.round(T.within_share * 100)}%<span> vs ${Math.round(T.chance_mean * 100)}% by chance</span>`;
  $("finding-text").innerHTML = `Armenian's stops and affricates come in sets of three, by where the mouth makes them. For these ${T.letters} letters, ${links} of the ${slots} nearest-neighbour slots in the model (each letter's two nearest) go to a letter of its own set: ${Math.round(T.within_share * 100)}%. Shuffling the letters ${fmt(T.permutations)} times gives ${Math.round(T.chance_mean * 100)}% on average, and ${beat === 0 ? `none of the ${fmt(T.permutations)} shuffles reached ${Math.round(T.within_share * 100)}% (p ≈ ${(1 / (T.permutations + 1)).toFixed(4)}, the smallest p this many shuffles can show)` : `${fmt(beat)} of the ${fmt(T.permutations)} shuffles did as well (p = ${T.p_value.toFixed(4)})`}. Measured on the model's full vectors, not on the 3D map. The model only ever saw spelling. <span class="grade">${D.grade}</span>`;
  $("sets").innerHTML = Object.entries(D.triads).map(([k, s]) => `<span><span lang="hyw">${s.split("").map((c) => `<span style="color:${PAL[c].hex.bright}">${BY[c].lower}</span>`).join(" ")}</span><em>${k}</em></span>`).join("");
  // which members link: first-second, second-third, first-third (the pair that sounds alike in Western)
  const pos = {}; Object.values(D.triads).forEach((s) => s.split("").forEach((c, j) => (pos[c] = [s, j])));
  const pc = { "01": 0, "12": 0, "02": 0 }, seen = new Set();
  for (const a of Object.keys(pos)) for (const n of (LAY.neighbours[a] || []).slice(0, K2)) {
    const b = n.symbol; if (!pos[b] || pos[a][0] !== pos[b][0]) continue;
    const e = [a, b].sort().join(""); if (seen.has(e)) continue; seen.add(e);
    pc[[pos[a][1], pos[b][1]].sort().join("")]++;
  }
  const ex = (j0, j1) => Object.entries(D.triads).map(([k, s]) => `<span style="color:${PAL[s[0]].set_ring}">${BY[s[j0]].lower} ${BY[s[j1]].lower}</span>`).join(", ");
  const nl = pc["01"] + pc["12"] + pc["02"];
  $("pairs").innerHTML = `Counted once per pair, those ${links} slots are ${nl} links: first and second members <span lang="hyw">(${ex(0, 1)})</span> ${pc["01"]}, second and third <span lang="hyw">(${ex(1, 2)})</span> ${pc["12"]}, first and third <span lang="hyw">(${ex(0, 2)})</span> ${pc["02"]}. The first and third are the pair that sounds the same in Western. No member pair stands out. <span class="grade">Measured</span>`;
  $("pairs2").innerHTML = `A test for later, not a finding. If Western spellings of foreign names were driving this (<span lang="hyw">Ճորճ Պուշ</span> against Eastern <span lang="hyw">Ջորջ Բուշ</span>), first-and-second links would outnumber the rest. ${pc["01"] > pc["12"] + 1 ? "Here they do, slightly, but" : `Here they do not (${pc["01"]} against ${pc["12"]}), and`} ${nl} links are too few to say; the letters-only Eastern and Western models will.`;

  // ---------------------------------------------------------------- how to read a letter (drawn from the real data for Բ)
  const exb = PAL["Բ"].hex;
  function threadsSVG() {
    const set = D.triads["lips"].split(""), at = { [set[0]]: [40, 70], [set[1]]: [100, 26], [set[2]]: [160, 70] };
    const extra = []; set.forEach((a) => (LAY.neighbours[a] || []).slice(0, 2).forEach((n) => { if (!at[n.symbol] && !extra.includes(n.symbol)) extra.push(n.symbol); }));
    extra.forEach((c, j) => (at[c] = [30 + (140 / Math.max(1, extra.length - 1 || 1)) * j + (extra.length === 1 ? 70 : 0), 104]));
    let o = "", seen = new Set();
    set.forEach((a) => (LAY.neighbours[a] || []).slice(0, 2).forEach((n) => { const b = n.symbol, e = [a, b].sort().join(""); if (seen.has(e)) return; seen.add(e);
      const inset = set.includes(b); o += `<line x1="${at[a][0]}" y1="${at[a][1]}" x2="${at[b][0]}" y2="${at[b][1]}" stroke="${inset ? SETHUE["lips"] : "#3a4a8a"}" stroke-width="${inset ? 2.6 : 1.2}"/>`; }));
    Object.entries(at).forEach(([c, [x, y]]) => { o += `<circle cx="${x}" cy="${y}" r="${set.includes(c) ? 5 : 3.5}" fill="${PAL[c].hex.bright}"/><text lang="hyw" x="${x + 8}" y="${y - 6}" font-family="Noto Serif Armenian, serif" font-weight="700" font-size="13" fill="${PAL[c].hex.bright}">${small(BY[c])}</text>`; });
    return `<svg viewBox="0 0 200 120" role="img" aria-label="The real nearest-neighbour threads of the lips set">${o}</svg>`;
  }
  const galSVG = (D.legend && D.legend.galaxy || []).map(([x, z, k, c, a]) => `<circle cx="${(100 + 88 * x).toFixed(1)}" cy="${(60 + 50 * z).toFixed(1)}" r="${[0.8, 1.3, 2.1][k]}" fill="${c}" opacity="${Math.min(1, a + 0.1).toFixed(2)}"/>`).join("");
  $("anatomy").innerHTML = [
    ["Star", `<svg viewBox="0 0 200 120" role="img" aria-label="The letter Բ drawn as a star"><image href="tex/star${IDX("Բ")}.webp" x="40" y="0" width="120" height="120"/></svg>`,
      "The capital in bold, inked in the letter's darkest colour and rimmed in gold leaf for Mashtots' 36, silver for the later Օ and Ֆ, and copper for the ligature և. Letters of a sound set wear their set's coloured ring. Click a star for its card."],
    ["Constellation", `<svg viewBox="0 0 200 120" role="img" aria-label="The constellation of Բ">${consSVG("Բ", 200, 120, 10, exb.bright, exb.hot)}</svg>`,
      "Around each star, the letter's own outline from the font, simplified into a few dozen stars and joined like a star chart. The sharpest corners are the brightest stars."],
    ["Galaxy", `<svg viewBox="0 0 200 120" role="img" aria-label="The galaxy of Բ, seen face on"><defs><radialGradient id="gcore"><stop offset="0" stop-color="${exb.hot}" stop-opacity=".9"/><stop offset="1" stop-color="${exb.hot}" stop-opacity="0"/></radialGradient></defs><circle cx="100" cy="60" r="18" fill="url(#gcore)"/>${galSVG}</svg>`,
      `Its galaxy. The number of arms follows the letter's row as a numeral: 2 arms for the units (<span lang="hyw">Ա</span> to <span lang="hyw">Թ</span>), 3 for the tens, 4 for the hundreds, 5 for the thousands. Size and star count follow how often the letter appears in held-out text, compressed by a square root, not to scale: <span lang="hyw">Ա</span> (${fmt(D.counts["Ա"] || 0)}) appears ${Math.round((D.counts["Ա"] || 1) / (D.counts["Ֆ"] || 1))} times as often as <span lang="hyw">Ֆ</span> (${fmt(D.counts["Ֆ"] || 0)}) but has ${((0.72 + 0.62) / (0.72 + 0.62 * Math.sqrt((D.counts["Ֆ"] || 1) / Math.max(...Object.values(D.counts))))).toFixed(1)}× the radius. <span lang="hyw">Օ</span> and <span lang="hyw">Ֆ</span>, with no numeral, are elliptical galaxies; <span lang="hyw">և</span> is two galaxies merging.`],
    ["Threads and sets", threadsSVG(),
      "Each thread joins a letter to its two nearest letters in the model, the same neighbours as the finding; this panel draws the real threads of the lips set. Threads inside a sound set glow in the set's colour; the rest are a faint web. The faint veils join the three letters of each set. The lines from <span lang=\"hyw\">և</span> to <span lang=\"hyw\">ե</span> and <span lang=\"hyw\">ւ</span> show its parts, not learned closeness. Tilt, spin, arm twist and dust colour are decoration."],
  ].map(([h, svg, p]) => `<article><h3>${h}</h3>${svg}<p>${p}</p></article>`).join("");

  // ---------------------------------------------------------------- the palette gallery
  $("gallery").innerHTML = ROWS.map((r) => { const P = PAL[r.upper]; return `<button type="button" class="tile" data-up="${r.upper}" style="--c-glow:${P.hex.body}33;--c-body:${P.hex.body}" aria-label="${glyph(r)}, ${r.name}, ${west(r)}" title="Eastern: ${r.latin}">
    <img src="tex/star${String(r.index).padStart(2, "0")}.webp" alt="" width="256" height="256" decoding="async"><div class="strip">${ROLES.map((k) => `<i style="background:${P.hex[k]}"></i>`).join("")}</div>
    <div class="lbl"><b lang="hyw">${glyph(r)}${r.group === "ligature" ? "" : " " + r.lower}</b><span>${west(r)}</span></div></button>`; }).join("");
  $("gallery").addEventListener("click", (e) => { const t = e.target.closest(".tile"); if (!t) return; card(t.dataset.up, true);
    const narrow = matchMedia("(max-width: 920px)").matches; if (narrow) $("card").focus({ preventScroll: true }); (narrow ? $("card") : $("scene")).scrollIntoView({ behavior: still() ? "auto" : "smooth", block: narrow ? "start" : "center" }); });

  // ---------------------------------------------------------------- the flat chart
  function chart(svg, w, h, fs = 1) {
    const P = D.positions, keys = Object.keys(P);
    const xs = keys.map((k) => P[k][V0][0]), ys = keys.map((k) => P[k][V0][1]);
    const pad = 46, minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
    const s = Math.min((w - 2 * pad) / (maxx - minx || 1), (h - 2 * pad) / (maxy - miny || 1));
    const X = (x) => w / 2 + (x - (minx + maxx) / 2) * s, Y = (y) => h / 2 - (y - (miny + maxy) / 2) * s;
    let out = `<defs>${keys.map((k) => `<radialGradient id="g${IDX(k)}"><stop offset="0" stop-color="${PAL[k].hex.bright}" stop-opacity=".55"/><stop offset="1" stop-color="${PAL[k].hex.body}" stop-opacity="0"/></radialGradient>`).join("")}</defs>`;
    const seen = new Set();
    for (const a of LAY.symbols) for (const n of LAY.neighbours[a].slice(0, 2)) {
      const e = [a, n.symbol].sort().join(""); if (seen.has(e)) continue; seen.add(e);
      const same = BY[a].triad && BY[a].triad === BY[n.symbol].triad;
      out += `<line x1="${X(P[a][V0][0])}" y1="${Y(P[a][V0][1])}" x2="${X(P[n.symbol][V0][0])}" y2="${Y(P[n.symbol][V0][1])}" stroke="${same ? SETHUE[BY[a].triad] : "#2b3768"}" stroke-width="${same ? 2 : 1}" opacity="${same ? 0.95 : 0.8}"/>`;
    }
    for (const k of keys) {
      const r = BY[k], x = X(P[k][V0][0]), y = Y(P[k][V0][1]), Cc = PAL[k].hex;
      out += `<g class="star" data-up="${k}" tabindex="0" role="button" aria-label="${glyph(r)} ${r.name}" style="cursor:pointer"><circle cx="${x}" cy="${y}" r="${22 * fs}" fill="url(#g${IDX(k)})"/><circle cx="${x}" cy="${y}" r="3" fill="${Cc.hot}"/>`;
      if (hand.has(k)) out += `<circle cx="${x}" cy="${y}" r="14" fill="none" stroke="${Cc.bright}" stroke-dasharray="3 3"/><text x="${x - 8}" y="${y + 26}" fill="${Cc.bright}" font-family="Spectral, serif" font-style="italic" font-size="${13 * fs}">by hand</text>`;
      out += `<text lang="hyw" x="${x + 8}" y="${y - 7}" fill="${Cc.bright}" stroke="${Cc.ink}" stroke-width="3" paint-order="stroke" font-family="Noto Serif Armenian, serif" font-weight="700" font-size="${19 * fs}">${small(r)}</text><title>${glyph(r)} ${r.name}</title></g>`;
    }
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.setAttribute("role", "group");
    svg.innerHTML = out;
  }
  const drawChart = () => { const P = D.positions, ks = Object.keys(P), xs = ks.map((k) => P[k][V0][0]), ys = ks.map((k) => P[k][V0][1]);
    const ar = (Math.max(...xs) - Math.min(...xs)) / (Math.max(...ys) - Math.min(...ys) || 1), narrow = matchMedia("(max-width: 560px)").matches;
    const w = narrow ? 420 : 900; chart($("chart"), w, Math.round((w - 92) / ar) + 92, narrow ? 1.35 : 1); };
  drawChart(); matchMedia("(max-width: 560px)").addEventListener("change", drawChart);
  $("chart-sub").textContent = `The same sky seen from the front, with depth dropped. The 3D map already bends the model's distances (stress ${LAY.stress}), so letters close on this chart are not always close in the model; the coloured lines are the true nearest neighbours inside a set.`;
  $("chart").addEventListener("click", (e) => { const g = e.target.closest(".star"); if (g) card(g.dataset.up, true); });
  $("chart").addEventListener("keydown", (e) => { const g = e.target.closest(".star"); if (g && (e.key === "Enter" || e.key === " ")) { card(g.dataset.up, true); e.preventDefault(); } });
  $("poster").innerHTML = `<img src="tex/star01.webp" alt="">`;

  // ---------------------------------------------------------------- sources
  const cs = D.count_source || {};
  $("sources").innerHTML = [
    `Similarities: ${D.source}. <span class="grade">${D.grade}</span>`,
    C.total_gb ? `Corpus: a ${C.total_gb} GB pool of Armenian text, ${C.western_gb} GB of it Western; ${C.tokens ? Math.round(C.tokens / 1e6) + " million training tokens, " : ""}Western share ${Math.round(C.western_share * 100)}%, so the Western pool was read ${C.western_epochs ?? "about 3"} times (${C.source}). <span class="grade">${C.grade}</span>` : "",
    `Layout: metric MDS of 1 − cosine, stress ${LAY.stress} (0 would be a perfect map; distances are approximate).`,
    D.counts && Object.keys(D.counts).length ? `Galaxy sizes: letter counts in ${cs.source}. <span class="grade">${cs.grade}</span> Radius 0.72 + 0.62√(n / max), stars 700 + 2300√(n / max). The ligature is not counted; it is drawn at the median size.` : `Galaxy sizes: no letter counts in this export; every galaxy has the same size.`,
    `On the counts, <span class="grade">Suspected</span>: the Western windows use classical spelling, which writes <span lang="hyw">և</span> as <span lang="hyw">ե + ւ</span> and many reformed <span lang="hyw">օ</span> as <span lang="hyw">աւ</span>, so the <span lang="hyw">Ե, Ւ</span> and <span lang="hyw">Ա</span> counts include those; <span lang="hyw">Ւ</span> is mostly the <span lang="hyw">ու</span> of u.`,
    D.placed_by_hand.length ? `Placed by hand, with dashed rings in the sky and on the flat chart: <span lang="hyw">${D.placed_by_hand.filter((c) => c !== "և").join(" ")}</span> (the model has vectors for them, but this export kept only the 36 × 36 similarities)${D.placed_by_hand.includes("և") ? `, and <span lang="hyw">և</span>, which the model has no single token for` : ""}.` : `Every symbol has a learned place.`,
    `Palettes: OKLCH, five colours per letter (ink, body, bright, hot, accent); glyphs: Noto Serif Armenian at weight 700 (SIL Open Font License).`,
    `Names and sounds: standard descriptions, typed by Claude, Western names first; a Western Armenian reader should check them, and the title.`,
  ].filter(Boolean).map((t) => `<li>${t}</li>`).join("");

  // ---------------------------------------------------------------- Eastern and Western (only with both dialect-only models)
  const X = D.extra || {};
  if (X.change_E_vs_W && X.symbols) {
    $("dialects").hidden = false;
    const MOVED = {}; X.symbols.forEach((c, i) => { MOVED[c === "և" ? "ԵՒ" : c] = X.moved_above_floor ? X.moved_above_floor[i] : X.change_E_vs_W[i]; });
    const order = Object.keys(MOVED).sort((a, b) => MOVED[b] - MOVED[a]);
    const top = Math.max(1e-9, ...order.map((k) => Math.abs(MOVED[k])));
    $("moved").innerHTML = order.map((k) => `<li data-up="${k}"><span class="l" lang="hyw" style="color:${PAL[k].hex.bright}">${small(BY[k])}</span><span class="bar"><i style="width:${Math.max(0, MOVED[k]) / top * 100}%;background:${PAL[k].hex.body}"></i></span><span>${MOVED[k].toFixed(3)}</span></li>`).join("");
    $("moved").addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) card(li.dataset.up, true); });
    const G = X.group_means || {};
    $("dia-text").innerHTML = `The letters model was trained twice more, on Eastern text only and on Western text only. The bars show how far each letter's similarities moved between the two${X.moved_above_floor ? ", above the seed floor" : ""}. Mean: spelling-reform letters ${G.reform ?? "–"}, sound-shift letters ${G.sound_shift ?? "–"}, the rest ${G.other ?? "–"}. <span class="grade">${D.grade}</span>`;
  }
  card("Բ");

  // ---------------------------------------------------------------- the live sky
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
  function toggle(btn, on, off) { btn.addEventListener("click", () => { const p = btn.getAttribute("aria-pressed") !== "true"; btn.setAttribute("aria-pressed", String(p)); (p ? on : off)(); }); }

  async function boot() {
    try {
      if (typeof X3D === "undefined") throw new Error("X_ITE did not load");
      const canvas = $("scene"), br = canvas.browser;
      dress(canvas);
      let n = 0; const keep = setInterval(() => { dress(canvas); if (++n > 20) clearInterval(keep); }, 250);
      await br.loadURL(new X3D.MFString("galaxy.xml"));
      dress(canvas);
      const sc = br.currentScene, node = (k) => { try { return sc.getNamedNode(k); } catch (e) { return null; } };
      const spin = node("SPIN_CLOCK"), gclocks = [0, 1, 2].map((j) => node(`GAL_CLOCK${j}`));
      const mq = matchMedia("(prefers-reduced-motion: reduce)");
      const apply = () => { const s = mq.matches; const nav = node("NAV"); if (nav) nav.transitionType = new X3D.MFString(s ? "TELEPORT" : "LINEAR");
        if (s) { spin.enabled = false; gclocks.forEach((c) => (c.enabled = false)); $("b-spin").setAttribute("aria-pressed", "false"); $("b-gspin").setAttribute("aria-pressed", "false"); } };
      apply(); mq.addEventListener("change", apply);
      toggle($("b-spin"), () => (spin.enabled = true), () => (spin.enabled = false));
      toggle($("b-gspin"), () => gclocks.forEach((c) => (c.enabled = true)), () => gclocks.forEach((c) => (c.enabled = false)));
      const each = (pre, v) => ROWS.forEach((r) => { const s = node(`${pre}${String(r.index).padStart(2, "0")}`); if (s) s.whichChoice = v; });
      const sw = (k, v) => { const s = node(k); if (s) s.whichChoice = v; };
      toggle($("b-gal"), () => each("GX", 0), () => each("GX", -1));
      toggle($("b-const"), () => each("C", 0), () => each("C", -1));
      toggle($("b-threads"), () => { sw("THREADS", 0); sw("LIG_LINKS", 0); }, () => { sw("THREADS", -1); sw("LIG_LINKS", -1); });
      toggle($("b-sets"), () => sw("SETS", 0), () => sw("SETS", -1));
      for (const [k, label] of [["VP_ALL", "Whole sky"], ["VP_SIDE", "From the side"], ["VP_NEAR", "Among the letters"]]) {
        const b = document.createElement("button"); b.type = "button"; b.textContent = label; b.className = "vp"; b.setAttribute("aria-pressed", String(k === "VP_ALL"));
        b.addEventListener("click", () => (node(k).set_bind = true)); $("vps").appendChild(b);
        try { node(k).addFieldCallback("vp" + k, "isBound", (on) => b.setAttribute("aria-pressed", String(!!on))); } catch (e) { /* older X_ITE: no live state */ }
      }
      const fit = () => { const a = canvas.clientWidth / Math.max(1, canvas.clientHeight), p = a < 1;      // X3D applies fieldOfView to the shorter side
        [["VP_ALL", 1.0, 0.72], ["VP_SIDE", 1.0, 0.72], ["VP_NEAR", 1.15, 0.95]].forEach(([k, fp, fl]) => { const v = node(k); if (v) v.fieldOfView = p ? fp : fl; });
        ROWS.forEach((r) => { const v = node(`VL${IDX(r.upper)}`); if (v) v.fieldOfView = p ? 0.95 : 0.8; }); };
      fit(); if (window.ResizeObserver) new ResizeObserver(fit).observe(canvas);
      flyTo = (up) => { const v = node(`VL${IDX(up)}`); if (v) { v.set_bind = true; $("status").textContent = `${glyph(BY[up])} ${BY[up].name}, ${west(BY[up])}. Drag to orbit it; "Whole sky" to go back.`; } };
      if (D.variants.length > 1) {
        const m = node("MORPH_CLOCK"); $("b-morph").hidden = false;
        toggle($("b-morph"), () => (m.enabled = true), () => (m.enabled = false));
      }
      for (const r of ROWS) { const t = node(`T${String(r.index).padStart(2, "0")}`); if (t) t.addFieldCallback("card", "touchTime", () => card(r.upper, false)); }
      $("poster").classList.add("gone");
      $("status").textContent = "Drag to turn the sky. Click a star for its card; pick a palette below to fly to it.";
    } catch (e) {
      $("status").textContent = "The live sky needs WebGL 2. The gallery and the flat chart below show the same letters.";
      console.error(e);
    }
  }
  if (document.readyState === "complete") boot(); else window.addEventListener("load", boot);
})();
</script>
"""


def write_page(out, info, xite_css):
    import alphabet as A
    data = dict(info, triads=A.TRIADS, versions=VERSIONS)
    page = (PAGE.replace("__XITE_CSS__", _css_for_shadow(xite_css)).replace("__TITLE_HY__", TITLE_HY)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    pathlib.Path(out, "index.html").write_text(page, encoding="utf-8")
    return out
