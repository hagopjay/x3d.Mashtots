#!/usr/bin/env python3
"""Write mashtots_letters_session.ipynb: the core cells MSH-0 .. MSH-9 and the letters cells LTR-1 .. LTR-8, as one Colab notebook.

usage: python3 -I make_letters_notebook.py
Use it on a G4 VM of its own (no Unreal lane on the same kernel); on the shared kernel paste the cells from the two .py files instead.
The cells are copied verbatim from mashtots_g4_cells.py and mashtots_letters_cells.py, so the notebook and the paste-in cells never drift.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def cells_of(path, keep=lambda title: True):
    src = open(os.path.join(HERE, path), encoding="utf-8").read()
    out = []
    for c in re.split(r"^# %%\s*$", src, flags=re.M)[1:]:
        c = c.strip("\n")
        t = next((ln for ln in c.splitlines() if ln.startswith("#@title")), "")
        if c.strip() and keep(t):
            out.append(c)
    return out


core = cells_of("mashtots_g4_cells.py", lambda t: bool(re.match(r"#@title MSH-[0-9] ", t)))
ltr = cells_of("mashtots_letters_cells.py")
intro = """# Mashtots letters session (build v1.2)

The letters study for the Western Armenian diaspora art project: a letters arm (one token per letter), Eastern-only and Western-only
letters models, and the Western ladder for the gap-closing piece. The plan and its forecasts are in `poc/LETTERS-PREREG.md`, written
before any letters run.

**Run on a G4 runtime, top to bottom.** First `MSH-0 .. MSH-9` with `MSH_PROFILE = "core"` (they rebuild the data and the tokenizers;
`MSH-7`, the token bill, can be skipped), then `LTR-1 .. LTR-8`. The code comes from `MyDrive/x3dlab/mashtots/mashtots_src_v1.2.tar.gz`
(its sha256 is pinned in `MSH-2`). Budget (Estimate): about 4 G4 hours, about 35 compute units; `LTR-4` prints the projection from
measured speed before anything long starts. Every long cell resumes from Drive."""
md = lambda s: dict(cell_type="markdown", metadata={}, source=s.splitlines(True))
code = lambda s: dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=s.splitlines(True))
nb = dict(nbformat=4, nbformat_minor=5, metadata=dict(accelerator="GPU", colab=dict(provenance=[], name="mashtots_letters_session.ipynb"),
                                                     kernelspec=dict(name="python3", display_name="Python 3"), language_info=dict(name="python")),
          cells=[md(intro), md("## Core cells: data, tokenizers, freeze")] + [code(c) for c in core]
          + [md("## Letters cells")] + [code(c) for c in ltr])
p = os.path.join(HERE, "mashtots_letters_session.ipynb")
with open(p, "w", encoding="utf-8") as fh:
    json.dump(nb, fh, ensure_ascii=False, indent=1)
print(p, len(core), "core cells +", len(ltr), "letters cells")
