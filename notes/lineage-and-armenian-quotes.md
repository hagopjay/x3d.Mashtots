# Lineage and quote matching for Armenian text (2026-11-16)

Method: Umair Ali Khan's article "How I Added Traceability in Structured Data Extraction with AI", and the GAIK toolkit's
`source_tracing` component (MIT). A value is kept with the exact quote it was read from; plain code, with no model, finds the quote in
the source (find), compares the value with it (compare) and says where it sits (locate). The answer is one of `verified`, `reworded`,
`check`, `unchecked`.

Read at `c817846`. Grades: Confirmed = I ran it or read the line; Likely = follows from Confirmed facts; Estimate = a rule I wrote that no
Armenian reader has looked at. **The Armenian in this note and in `poc/provenance/armenian_quote/` was typed by an AI; a Western
Armenian reader should check it before anything here is relied on.**

## Why this matters for this project

The repo already says what it does not know: the README asks an Armenian reader to check the Armenian text, and the data card lists the
sources. What it cannot yet say, per text or per quote, is source, place in the source, licence and rights holder in a way a program can
check. That matters because the project is a social art project for the Western diaspora: people bring texts, and "withdrawing removes
your answers from every later release" (`poc/participation/CONSENT-AND-CREDIT.md`) is a promise a check should be able to keep.

## What exists (Confirmed)

* `poc/DATA-CARD.md` is a prose table of 20 sources; `poc/mp_data.py` `SOURCES` carries the same facts as code, pinned by revision (Hugging
  Face) or by tag `r2.18` (Universal Dependencies). Facts about one source sit in three places: the table, `SOURCES` and the batch's
  free-text `text_licences`.
* No file hash. `_get` returns any existing non-empty file; `fetch` logs bytes, seconds and revision, not sha-256.
* The pools write `{"t", "s", "o"}` per document. The document id and the dedupe hash are computed and then dropped, so the pool line
  number is the only locator. Dropped documents are counted per source, never listed.
* There is no CI and there are no tests outside `poc/letters/alphabet.py --test` and the notebook's Doctor cell.

## Why a plain tokenizer is not enough for Armenian (Confirmed; Python 3.13, Unicode 15.1)

* **One letter, two encodings.** U+0587, the ligature ech-yiwn, is one code point. `casefold()` and NFKC turn it into two (U+0565 U+0582);
  `lower()`, NFC and NFD leave it alone. So `"եւ" == "և"` is false, and `upper().lower()` does not round-trip. Other Unicode folding has
  the same trap with the Latin ligature "fi".
* **It sorts the varieties.** In UD sentences U+0587 occurs in 37.6% of Eastern (hy dev, 575 sentences) and in 0 of 693 Western (hyw dev)
  and 0 of 423 Grabar (xcl dev), which write the two-letter form (22.2% and 80.1% of those sentences contain a standalone եւ). A quote
  check must not treat the two spellings as different words.
* **`\w` breaks words.** The marks U+055B, U+055C and U+055E (emphasis, exclamation, question) and U+055A (apostrophe) are not `\w`, but
  they sit inside the word. A `\w+` tokenizer, as in GAIK's matcher and in `mp_data.py` `_WORD`, cuts "ինչո՞ւ" into "ինչո" and "ւ".
  UD cuts the mark off as its own token, so even "word" differs between UD and `\w+`.
* **Apostrophes.** Western Wikipedia writes the apostrophe as ASCII `'` or U+2019 (44 times in a 500-article sample) and U+055A once; the
  Western treebank uses U+055A 88 times; U+02BC is a letter to `\w`.

### Measured: how a quote breaks (3,000 windows of 4 to 8 words cut from the Western dev set, then damaged; seed 20261116)

| Damage to the quote | Windows | GAIK's matcher passes | The normaliser here |
|---|---|---|---|
| upper case, title case, doubled spaces | 3,000 | 100% | 100% verified |
| two letters typed as the ligature | 485 | 0.0% | 100% verified |
| apostrophe turned into U+02BC | 117 | 0.0% | 100% verified |
| emphasis marks deleted | 274 | 15.0% | 100% verified |
| all punctuation stripped | 2,206 | 82.0% | 91.6% verified, 8.4% reworded |
| rewritten in the reformed spelling (circular: the rules are the fold's own) | 2,388 | 0.0% | 4.6% verified, 95.4% reworded |

The baseline is GAIK's matcher copied unchanged from commit `394a94b`. False accepts (a quote cut from a different text must be `check`):
one-word quotes are accepted 23% of the time against a random Western page, two words 0.8% to 1%, three words 0.13% or less, four words
0%. The data supports a floor of three words for `verified`; GAIK's default is one.

## The normaliser (a prototype, `poc/provenance/armenian_quote/`)

`armenian_norm.py`, 192 lines, standard library only. Per word, on the original string so offsets stay original: tokenise (letters,
combining marks and digits; apostrophe forms always break; the emphasis marks stay inside and are dropped from the key), then the basic
fold `NFKC(casefold(NFKC(word)))`, then an orthography fold. A match by the basic fold is `verified`; one that needs the orthography fold or
a spacing repair is `reworded` and lists the respelled words as evidence. It can say `reworded` and never `verified` for a respelling,
because the fold is many-to-one: 0.42% of distinct Western word types collide, mostly real inflection pairs (present and past forms that
differ only in e and ē).

**The orthography rules are an Estimate.** They were written from the repo's own marker list (`mp_data.py`) and `alphabet.py`, not by a
reader. Order: non-initial է to ե; իւ to յու; եա to յա; ոյ to ույ; ւ not after ո to վ; two lexical exceptions. Word-initial յ to հ is left out
on purpose (it merges real Western pairs). The biggest single rule is non-initial է: Western word types found in the Eastern dev
vocabulary go from 31.3% to 35.4% of tokens.

Results (Confirmed): `35 passed` with the real-text test, `34 passed, 1 skipped` without it (it needs `ARM_UD_DIR` pointing at the
ArmTDP dev file, which is not shipped). 34 unit tests plus one over 21 hand-written vectors; 300 shouted-and-ligatured windows from the real
text all verify and their spans re-tokenise to the quote. A 10-mutant spot check killed 9; the survivor (casefold for lower) is
equivalent because NFKC already runs first. Speed: 0.04 ms per hit and 0.06 ms per miss on a 2 KB source.

Known misses: Grabar աւ to օ, lexical reforms beyond the two listed, textual variants (correctly `check`), Western and Eastern morphology
and vocabulary, foreign-name spellings, Armenian numerals (letters) against digits.

## The Landing's two texts against the project's licensed corpus (Confirmed)

Source: UD Classical Armenian CAVaL r2.18, train, dev and test, 4,781 sentences. Texts as `mp_common.py` `LANDING_TEXTS` writes them.

* The Lord's Prayer, 10 clauses of at least two words: 7 `verified`, 3 `check`. The three that fail are ordinary: a word CAVaL lacks, a
  textual variant of "եկեսցէ", and the liturgical "ԱՄԷՆ". The whole prayer as one quote is `check`.
* Proverbs 1:2, 2 of 2 clauses `check`, as expected: CAVaL holds only the Gospels and a history (MX.Hist), so there is no open witness for Proverbs
  in the data card (Likely).
* **A rights question, not a technical one.** The only open witness for the prayer is CAVaL, which is CC BY-NC-SA 4.0. The prayer is old,
  and `landing/README.md` names the printed source (dominicweb.eu). A ledger should record both and let a person decide; it must not
  silently make the Landing non-commercial and share-alike.
* The classical spelling "այսաւր" (CAVaL) and the README's "այսօր" differ; the fold deliberately does not map աւր to օր.

## Decontamination (Likely, not changed)

The 8-gram keys in `mp_data.py` (`word_ngrams`) use the same `\w+` tokenizer. Under the repo's keys, a retyped copy of a Western sentence
shares no key with the original in 31.5% of cases when the emphasis marks are removed, and in 16.2% when the ligature is typed as two
letters; under the normaliser it is 0% in both. The pools are not in the checkout, so this could not be measured on them. The pre-registration
is frozen, so any change needs a dated deviation note first. Nothing was changed.

## Proposals, not built

| id | what | size |
|---|---|---|
| M1 | A Western Armenian reader signs off the orthography rules and the 21 vectors; only then does the module leave `poc/provenance/` | S |
| M2 | `poc/provenance/sources.lock.json`: one row per source (revision or tag, files with size and sha-256, SPDX licence, NC and SA flags, variety, credit), with a test that the three places agree; `_get` checks the hash | S |
| M3 | A quote ledger `quotes.jsonl`, one row per Armenian quote that appears in an artefact (Landing clauses, captions, annotation items): text, where it is used, source id, locator, verdict, tier, licence. A checker re-reads the pinned source and compares. An artefact's licence is the most restrictive of its quotes' | M |
| M4 | Keep the document id and dedupe hash in the pool lines, so a withdrawal can be checked: delete a contributor's rows, rebuild, assert none remain | S |
| M5 | `_SENT_SPLIT` in `mp_data.py` lacks the Armenian full stop U+2024 that Western Wikipedia uses (123 times in the sample), so run-on text slips past the 8 to 40 word filter (Likely) | S |

## Open questions for the project owner

1. Should the prayer be traced to CAVaL (non-commercial, share-alike) or to the printed source, and who is the Western Armenian reader?
2. May the decontamination tokenizer change after the pre-registration was frozen, with a dated deviation note?
3. The galaxy edition (`poc/letters/galaxy.py`) is not in this checkout; a ledger should be seeded against it when it lands.
4. The Wikipedia sample was 500 rows of an unpinned server revision; the full pools would give true apostrophe and ligature rates.

## Sources

Umair Ali Khan's article above. GAIK toolkit, commit `394a94b` (MIT): the verdict names and the baseline matcher. UD Western Armenian
ArmTDP, UD Armenian ArmTDP (CC BY-SA 4.0) and UD Classical Armenian CAVaL (CC BY-NC-SA 4.0), tag `r2.18`, read in scratch and not copied
into this repo.
