#!/usr/bin/env python3
"""The page around the letter constellation: the live X3D sky (X_ITE), a flat star chart, the letter card, the finding and the grades.

Called by constellation.build(). Writes index.html next to constellation.xml. The page works in the claude.ai viewer: X_ITE loads from
jsDelivr, its stylesheet is inlined into its shadow root (the viewer blocks CDN stylesheets), and its helper files are served from xite/.
"""
from __future__ import annotations

import json
import pathlib
import re

TITLE_HY = "Տառերու համաստեղութիւն"          # Western Armenian, classical spelling; to be checked by a Western Armenian reader


def _css_for_shadow(css):
    css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
    css = re.sub(r"url\([^)]*\)", "none", css)
    return css


PAGE = r"""<title>Letter Constellation</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Armenian:wght@400;600&family=Spectral:ital,wght@0,400;0,500;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<script>
/* The viewer lets a page fetch only its own files, so X_ITE's helper files are served from xite/. */
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
/* Layout: a night sky on lapis, the live scene first, then the letter card beside it, then the flat chart and the notes.
   One deliberate dark look (an illuminated manuscript at night), so no light variant. */
:root {
  color-scheme: dark;
  --lapis: #0b1430;        /* page ground */
  --lapis-2: #121d42;      /* panels */
  --ink: #e9e3d3;          /* text */
  --ink-2: #a9a69c;        /* quiet text */
  --gold: #f2c46b;         /* Mashtots' 36 */
  --vermilion: #e8553c;    /* lips */
  --saffron: #f6a92e;      /* back of the tongue */
  --turquoise: #41ccc7;    /* teeth */
  --rose: #e873a8;         /* teeth, hissing */
  --verdigris: #8dd15a;    /* palate, hushing */
  --silver: #c7d6f2;       /* the later two */
  --copper: #f5945f;       /* the ligature */
  --rule: #24305c;
  --f-hy: "Noto Serif Armenian", "Noto Serif", serif;
  --f-text: "Spectral", Georgia, serif;
  --f-data: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}
html, body { background: var(--lapis); color: var(--ink); }
body { font-family: var(--f-text); font-size: 17px; line-height: 1.55; }
.wrap { max-width: 1180px; margin: 0 auto; padding-block: 28px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); display: grid; gap: 28px; }
header { display: grid; gap: 6px; }
.hy { font-family: var(--f-hy); color: var(--gold); font-size: clamp(30px, 5vw, 52px); line-height: 1.1; margin: 0; text-wrap: balance; letter-spacing: 0.01em; }
h1 { font-family: var(--f-text); font-weight: 500; font-size: clamp(20px, 2.6vw, 26px); margin: 0; color: var(--ink); }
.lede { max-width: 68ch; color: var(--ink-2); margin: 4px 0 0; }
.stage { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 20px; align-items: start; }
@media (max-width: 860px) { .stage { grid-template-columns: minmax(0, 1fr); } }
.sky { position: relative; background: radial-gradient(ellipse at 50% 40%, #16245a 0%, var(--lapis) 70%); border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; aspect-ratio: 4 / 3; max-width: 100%; }
x3d-canvas { width: 100%; height: 100%; display: block; }
.sky .poster { position: absolute; inset: 0; display: grid; place-items: center; pointer-events: none; transition: opacity .6s; }
.sky .poster.gone { opacity: 0; }
.controls { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
button { font-family: var(--f-data); font-size: 13px; color: var(--ink); background: var(--lapis-2); border: 1px solid var(--rule); border-radius: 4px; padding: 6px 10px; cursor: pointer; }
button[aria-pressed="true"] { border-color: var(--gold); color: var(--gold); }
button:focus-visible { outline: 2px solid var(--gold); outline-offset: 2px; }
.status { font-family: var(--f-data); font-size: 12px; color: var(--ink-2); margin-top: 6px; min-height: 1.4em; }
.card { background: var(--lapis-2); border: 1px solid var(--rule); border-radius: 6px; padding: 18px; display: grid; gap: 10px; min-width: 0; }
.card .glyph { font-family: var(--f-hy); font-size: 72px; line-height: 1; color: var(--gold); }
.card .glyph small { font-size: 36px; color: var(--ink-2); margin-left: 8px; }
.card dl { display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; margin: 0; font-size: 15px; }
.card dt { color: var(--ink-2); font-family: var(--f-data); font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; padding-top: 3px; }
.card dd { margin: 0; }
.card .hint { color: var(--ink-2); font-size: 14px; }
.ipa { font-family: var(--f-data); }
.finding { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 20px; align-items: center; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); padding-block: 22px; }
@media (max-width: 640px) { .finding { grid-template-columns: minmax(0, 1fr); } }
.big { font-family: var(--f-data); font-size: clamp(40px, 7vw, 64px); color: var(--gold); line-height: 1; font-variant-numeric: tabular-nums; }
.big span { font-size: 0.4em; color: var(--ink-2); }
.finding p { margin: 0; max-width: 70ch; }
.sets { display: flex; flex-wrap: wrap; gap: 10px 22px; margin-top: 10px; font-family: var(--f-hy); font-size: 22px; }
.sets span { display: inline-flex; gap: 6px; align-items: baseline; }
.sets em { font-family: var(--f-data); font-style: normal; font-size: 12px; color: var(--ink-2); }
.chart-wrap { overflow-x: auto; }
svg.chart { width: 100%; min-width: 560px; height: auto; display: block; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 18px; font-size: 14px; color: var(--ink-2); }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.notes { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; }
.notes section { min-width: 0; }
.notes h2 { font-family: var(--f-data); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-2); margin: 0 0 8px; }
.notes p, .notes li { font-size: 15px; margin: 0 0 8px; }
.notes ul { padding-left: 18px; margin: 0; }
.grade { font-family: var(--f-data); font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; border: 1px solid var(--rule); border-radius: 3px; padding: 1px 5px; color: var(--ink-2); white-space: nowrap; }
.dialects { margin: 28px 0; }
.dialects h2 { font-family: var(--f-data); font-size: 12px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-2); margin: 0 0 8px; }
.dialects > p { max-width: 68ch; }
.dia-sets { display: flex; flex-wrap: wrap; gap: 10px 26px; font-family: var(--f-data); font-size: 13px; margin: 10px 0 14px; }
.dia-sets b { font-size: 20px; font-weight: 500; color: var(--ink); margin-right: 6px; }
.moved { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 4px 18px; }
.moved li { display: grid; grid-template-columns: 2.2em 1fr 3.6em; align-items: center; gap: 8px; font-family: var(--f-data); font-size: 12px; cursor: pointer; }
.moved .l { font-family: var(--f-hy); font-size: 18px; }
.moved .bar { height: 6px; border-radius: 3px; background: var(--rule); position: relative; overflow: hidden; }
.moved .bar i { position: absolute; inset: 0 auto 0 0; border-radius: 3px; }
.moved .v { text-align: right; color: var(--ink-2); }
@media (prefers-reduced-motion: reduce) { .sky .poster { transition: none; } }
</style>

<div class="wrap">
  <header>
    <p class="hy" lang="hyw">__TITLE_HY__</p>
    <h1>Letter Constellation</h1>
    <p class="lede">Each star is an Armenian letter. A small language model read four gigabytes of Armenian and learned a vector for every letter; letters it treats alike sit close together here. Nobody told it how the letters sound.</p>
  </header>

  <div class="stage">
    <div>
      <div class="sky">
        <x3d-canvas id="scene" splashScreen="false" notifications="false" contextMenu="false" timings="false" cache="true"></x3d-canvas>
        <div class="poster" id="poster" aria-hidden="true"></div>
      </div>
      <div class="controls" role="group" aria-label="Scene controls">
        <button type="button" id="b-spin" aria-pressed="true">Turning</button>
        <button type="button" id="b-threads" aria-pressed="true">Nearest-neighbour threads</button>
        <button type="button" id="b-sets" aria-pressed="true">The five sets</button>
        <span id="vps" class="controls" style="margin:0"></span>
        <button type="button" id="b-morph" aria-pressed="false" hidden>Eastern ⇄ Western</button>
      </div>
      <p class="status" id="status">Loading the sky…</p>
    </div>
    <aside class="card" id="card" aria-live="polite"></aside>
  </div>

  <div class="finding">
    <div class="big" id="big"></div>
    <div>
      <p id="finding-text"></p>
      <div class="sets" id="sets"></div>
    </div>
  </div>

  <section>
    <div class="chart-wrap"><svg class="chart" id="chart" role="img" aria-label="Flat star chart of the letters, seen from the front"></svg></div>
    <div class="legend" id="legend"></div>
  </section>

  <section class="dialects" id="dialects" hidden>
    <h2>Eastern and Western skies</h2>
    <p id="dia-text"></p>
    <div class="dia-sets" id="dia-sets"></div>
    <ol class="moved" id="moved"></ol>
    <p class="hint" id="dia-key"></p>
  </section>

  <div class="notes">
    <section>
      <h2>How to read it</h2>
      <p>Drag to turn the sky; click a letter to read its card. Threads join each letter to its two nearest letters in the model. A coloured thread means both ends belong to the same set of three.</p>
      <p>Gold letters are Mashtots' 36. Silver Օ and Ֆ arrived around the 12th century. Copper և is the ligature of ե and ւ.</p>
    </section>
    <section>
      <h2>Where the numbers come from</h2>
      <ul id="sources"></ul>
    </section>
    <section>
      <h2>What is next</h2>
      <p id="next">A letters-only model, trained once on Eastern and once on Western text, will give every symbol a learned place, including Օ, Ֆ and և. The sky will then move between the two dialects. The Western half grows as the diaspora's texts are added.</p>
    </section>
  </div>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(() => {
  const $ = (id) => document.getElementById(id);
  const D = JSON.parse($("data").textContent);
  const V0 = D.variants[0];
  const LAY = D.layout[V0];
  const ROWS = D.letters;
  const BY = Object.fromEntries(ROWS.map((r) => [r.upper, r]));
  const COL = { "lips": "--vermilion", "back of the tongue": "--saffron", "teeth": "--turquoise", "teeth, hissing": "--rose", "palate, hushing": "--verdigris" };
  const colour = (r) => r.group === "later" ? "var(--silver)" : r.group === "ligature" ? "var(--copper)" : r.triad ? `var(${COL[r.triad]})` : "var(--gold)";
  const hand = new Set(D.placed_by_hand.map((c) => c === "և" ? "ԵՒ" : c));
  const X = D.extra || {};
  const MOVED = {};                                   // symbol -> {moved, raw, floor}: E vs W row change minus the seed floor
  if (X.change_E_vs_W && X.symbols) X.symbols.forEach((c, i) => {
    MOVED[c === "և" ? "ԵՒ" : c] = { raw: X.change_E_vs_W[i], floor: X.noise_floor ? X.noise_floor[i] : null, moved: X.moved_above_floor ? X.moved_above_floor[i] : null };
  });

  // ---------------------------------------------------------------- the letter card
  function card(up) {
    const r = BY[up];
    const nb = (LAY.neighbours[up] || []).map((n) => `<span style="font-family:var(--f-hy)">${BY[n.symbol].lower}</span> <span class="ipa">${n.cosine.toFixed(2)}</span>`).join(" · ");
    const placed = hand.has(up) ? `<p class="hint">Placed by hand in this version: the model behind this sky has no learned place for it yet.</p>` : "";
    $("card").innerHTML = `
      <div class="glyph">${r.group === "ligature" ? "Եւ" : r.upper}<small>${r.lower}</small></div>
      <dl>
        <dt>Name</dt><dd><span style="font-family:var(--f-hy)">${r.name}</span> (${r.latin})</dd>
        ${r.numeral ? `<dt>Numeral</dt><dd class="ipa">${r.numeral.toLocaleString("en-US")}</dd>` : ""}
        <dt>Eastern</dt><dd class="ipa">[${r.ipa_east}]</dd>
        <dt>Western</dt><dd class="ipa">[${r.ipa_west}]${r.sound_differs ? ` <span class="grade">differs</span>` : ""}</dd>
        ${r.triad ? `<dt>Set</dt><dd>${r.triad} <span style="font-family:var(--f-hy)">${Object.values(D.triads).find((s) => s.includes(up)).split("").map((c) => BY[c].lower).join(" ")}</span></dd>` : ""}
        ${nb ? `<dt>Nearest</dt><dd>${nb}</dd>` : ""}
        ${r.reform ? `<dt>Spelling</dt><dd>${r.reform}</dd>` : ""}
        ${MOVED[up] ? `<dt>E ⇄ W</dt><dd class="ipa">moved ${MOVED[up].raw.toFixed(3)}${MOVED[up].floor != null ? `, seed floor ${MOVED[up].floor.toFixed(3)}` : ""}</dd>` : ""}
      </dl>${placed}`;
  }

  // ---------------------------------------------------------------- the finding
  const T = LAY.triads;
  $("big").innerHTML = `${Math.round(T.within_share * 100)}%<span> vs ${Math.round(T.chance_mean * 100)}% by chance</span>`;
  $("finding-text").innerHTML = `Armenian's stops and affricates come in sets of three, by where the mouth makes them. For these ${T.letters} letters, ${Math.round(T.within_share * 100)}% of each letter's two nearest neighbours in the model come from its own set. Shuffling the letters ${T.permutations.toLocaleString("en-US")} times gives ${Math.round(T.chance_mean * 100)}% on average${T.p_value < 0.01 ? ", and almost no shuffle came close" : T.p_value < 0.05 ? ", and few shuffles did as well" : ", and many shuffles did as well, so this sky shows no sign of the sets"} (p = ${T.p_value < 0.001 ? T.p_value.toExponential(1) : T.p_value.toFixed(3)}). The model only ever saw spelling. <span class="grade">${D.grade}</span>`;
  $("sets").innerHTML = Object.entries(D.triads).map(([k, s]) => `<span style="color:var(${COL[k]})">${s.split("").map((c) => BY[c].lower).join(" ")} <em>${k}</em></span>`).join("");

  // ---------------------------------------------------------------- the flat chart (x right, y up), also the poster
  function chart(svg, w, h, labels) {
    const P = D.positions;
    const keys = Object.keys(P);
    const xs = keys.map((k) => P[k][V0][0]), ys = keys.map((k) => P[k][V0][1]);
    const pad = 40, minx = Math.min(...xs), maxx = Math.max(...xs), miny = Math.min(...ys), maxy = Math.max(...ys);
    const s = Math.min((w - 2 * pad) / (maxx - minx || 1), (h - 2 * pad) / (maxy - miny || 1));
    const X = (x) => w / 2 + (x - (minx + maxx) / 2) * s, Y = (y) => h / 2 - (y - (miny + maxy) / 2) * s;
    let out = "";
    const seen = new Set();
    for (const a of LAY.symbols) for (const n of LAY.neighbours[a].slice(0, 2)) {
      const e = [a, n.symbol].sort().join(""); if (seen.has(e)) continue; seen.add(e);
      const same = BY[a].triad && BY[a].triad === BY[n.symbol].triad;
      out += `<line x1="${X(P[a][V0][0])}" y1="${Y(P[a][V0][1])}" x2="${X(P[n.symbol][V0][0])}" y2="${Y(P[n.symbol][V0][1])}" stroke="${same ? colour(BY[a]) : "var(--rule)"}" stroke-width="${same ? 1.6 : 1}" opacity="${same ? 0.9 : 0.8}"/>`;
    }
    for (const k of keys) {
      const r = BY[k], x = X(P[k][V0][0]), y = Y(P[k][V0][1]);
      out += `<g class="star" data-up="${k}" style="cursor:pointer"><circle cx="${x}" cy="${y}" r="13" fill="${colour(r)}" opacity="0.16"/><circle cx="${x}" cy="${y}" r="2.4" fill="${colour(r)}"/>`;
      if (labels) out += `<text x="${x + 7}" y="${y - 6}" fill="${colour(r)}" font-family="var(--f-hy)" font-size="17">${r.lower}</text>`;
      out += `<title>${r.upper}${r.lower} ${r.name}</title></g>`;
    }
    svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
    svg.innerHTML = out;
  }
  chart($("chart"), 900, 520, true);
  $("chart").addEventListener("click", (e) => { const g = e.target.closest(".star"); if (g) card(g.dataset.up); });
  const poster = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  poster.setAttribute("width", "100%"); poster.setAttribute("height", "100%");
  $("poster").appendChild(poster); chart(poster, 800, 600, true);
  $("legend").innerHTML = [["var(--gold)", "Mashtots' 36"], ...Object.entries(COL).map(([k, v]) => [`var(${v})`, k]), ["var(--silver)", "later arrivals Օ Ֆ"], ["var(--copper)", "ligature և"]]
    .map(([c, t]) => `<span><i style="background:${c}"></i>${t}</span>`).join("");
  $("sources").innerHTML = [
    `Similarities: ${D.source}. <span class="grade">${D.grade}</span>`,
    `Layout: metric MDS of 1 − cosine, stress ${LAY.stress} (0 would be a perfect map; distances are approximate).`,
    D.placed_by_hand.length ? `Placed by hand, not learned yet: ${D.placed_by_hand.join(" ")}.` : `Every symbol has a learned place.`,
    `Names and sounds: standard descriptions, typed by Claude; a Western Armenian reader should check them, and the title.`,
  ].map((t) => `<li>${t}</li>`).join("");
  card("Բ");

  // ---------------------------------------------------------------- Eastern and Western (only when both dialect-only models exist)
  if (Object.keys(MOVED).length) {
    $("dialects").hidden = false;
    const tri = X.triads || {}, G = X.group_means || {};
    const pct = (v) => v == null ? "–" : `${Math.round(v * 100)}%`;
    $("dia-sets").innerHTML = [["EW", "mixed"], ["E", "Eastern only"], ["W", "Western only"]].filter(([k]) => k in tri)
      .map(([k, t]) => `<span><b>${pct(tri[k])}</b>five-sets share, ${t}</span>`).join("");
    const useFloor = Object.values(MOVED).some((m) => m.moved != null);
    const val = (m) => useFloor ? m.moved : m.raw;
    const order = Object.keys(MOVED).sort((a, b) => val(MOVED[b]) - val(MOVED[a]));
    const top = Math.max(1e-9, ...order.map((k) => Math.abs(val(MOVED[k]))));
    const tint = (k) => { const r = BY[k]; return r.reform ? "var(--copper)" : r.sound_differs ? "var(--turquoise)" : "var(--gold)"; };
    $("moved").innerHTML = order.map((k) => { const v = val(MOVED[k]);
      return `<li data-up="${k}"><span class="l" style="color:${tint(k)}">${BY[k].group === "ligature" ? "և" : BY[k].lower}</span><span class="bar"><i style="width:${Math.max(0, v) / top * 100}%;background:${tint(k)}"></i></span><span class="v">${v.toFixed(3)}</span></li>`; }).join("");
    $("moved").addEventListener("click", (e) => { const li = e.target.closest("li"); if (li) card(li.dataset.up); });
    const gm = (k) => G[k] == null ? "–" : G[k].toFixed(3);
    $("dia-text").innerHTML = `The same letters model was trained twice more, once on Eastern text only and once on Western text only. Each letter's list of similarities was compared between the two. ${useFloor ? "The bars show how much more a letter moved than two runs of one dialect differ by chance (the seed floor)." : "The bars show the raw change; a second seed would give the floor."} Mean movement: spelling-reform letters ${gm("reform")}, sound-shift letters ${gm("sound_shift")}, the rest ${gm("other")}. <span class="grade">${D.grade}</span>`;
    $("dia-key").innerHTML = `<span style="color:var(--copper)">Copper</span>: spelled differently in the 1922 reform. <span style="color:var(--turquoise)">Turquoise</span>: sounds different in Western. Gold: neither. Click a letter for its card.`;
    $("next").textContent = "The Western half grows as the diaspora's texts are added: the gap-closing piece follows the Western score as Western text grows.";
  }

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
      await br.loadURL(new X3D.MFString("constellation.xml"));
      dress(canvas);
      const sc = br.currentScene, node = (k) => sc.getNamedNode(k);
      const spin = node("SPIN_CLOCK");
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) { spin.enabled = false; $("b-spin").setAttribute("aria-pressed", "false"); }
      toggle($("b-spin"), () => (spin.enabled = true), () => (spin.enabled = false));
      toggle($("b-threads"), () => (node("THREADS").whichChoice = 0), () => (node("THREADS").whichChoice = -1));
      toggle($("b-sets"), () => (node("SETS").whichChoice = 0), () => (node("SETS").whichChoice = -1));
      for (const [k, label] of [["VP_ALL", "Whole sky"], ["VP_SIDE", "Side"], ["VP_NEAR", "Among the letters"]]) {
        const b = document.createElement("button"); b.type = "button"; b.textContent = label;
        b.addEventListener("click", () => (node(k).set_bind = true)); $("vps").appendChild(b);
      }
      if (D.variants.length > 1) {
        const m = node("MORPH_CLOCK"); $("b-morph").hidden = false;
        toggle($("b-morph"), () => (m.enabled = true), () => (m.enabled = false));
      }
      for (const r of ROWS) {
        let t; try { t = node(`T${String(r.index).padStart(2, "0")}`); } catch (e) { continue; }
        t.addFieldCallback("card", "touchTime", () => card(r.upper));
      }
      $("poster").classList.add("gone");
      $("status").textContent = "Drag to turn the sky. Click a letter.";
    } catch (e) {
      $("status").textContent = "The live sky needs WebGL 2. The flat chart below shows the same map.";
      console.error(e);
    }
  }
  if (document.readyState === "complete") boot(); else window.addEventListener("load", boot);
})();
</script>
"""


def write_page(out, info, xite_css):
    import alphabet as A
    data = dict(info, triads=A.TRIADS)
    page = (PAGE.replace("__XITE_CSS__", _css_for_shadow(xite_css))
            .replace("__TITLE_HY__", TITLE_HY)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    pathlib.Path(out, "index.html").write_text(page, encoding="utf-8")
    return out
