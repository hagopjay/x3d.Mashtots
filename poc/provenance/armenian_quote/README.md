# armenian_quote (prototype)

Quote matching for Armenian text: find a quote in a source, with a verdict (`verified`, `reworded`, `check`), the character span in the
original source and the respelled words as evidence. Standard library only. Not imported by the PoC.

**Estimate.** The orthography rules (`ORTHO_RULES`) and `armenian_vectors.json` were written by an AI from the repo's own marker list, not
by a reader. A Western Armenian reader must check them before this is used for anything that matters. See
[../../../notes/lineage-and-armenian-quotes.md](../../../notes/lineage-and-armenian-quotes.md).

```
python3 -I -m pytest -q poc/provenance/armenian_quote
ARM_UD_DIR=<folder holding hyw_armtdp-ud-dev.conllu> python3 -I -m pytest -q poc/provenance/armenian_quote   # adds the real-text test
```

Last result: `34 passed, 1 skipped` without the corpus and `35 passed` with it (UD Western Armenian ArmTDP dev, release 2.18, CC BY-SA 4.0,
not shipped here), Python 3.13.

Invisible Armenian marks are written as `\u` escapes in the source on purpose: literal characters are unreadable in a diff.
