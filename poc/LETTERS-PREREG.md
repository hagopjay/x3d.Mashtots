# The letters study: pre-registration (exploratory, written 16 Nov 2026, before any letters run)

This study is **exploratory**. It sits beside the frozen PREREG.md (H1-H6) and never re-scores H2 or any other pre-registered hypothesis.
It is written down before its first run so that its numbers can be defended: every run is reported, no run is repeated to change a
result, and the forecasts below are scored with the Brier score afterwards. The cell LTR-5 freezes this file (sha256) before any model trains.

Owner's goal (16 Nov 2026): a social art project for the Western Armenian diaspora. A **letter constellation** (each Armenian letter
placed in 3D by what a model learned about it, Eastern and Western side by side) and a **gap-closing piece** (the Western gap shown
closing as Western text is added). The science below is what those two pieces stand on.

## 1. Arms and data

* `letters`: one token per character from a fixed set of 185 symbols (the 38 letters in both cases, the ligature և, Latin letters,
  digits, ASCII and Armenian punctuation, space, newline) plus 256 byte-fallback ids and `<eos>`: 442 ids (`mp_letters.py`).
  Unlike `bytes`, an Armenian letter is one token, not two halves of its UTF-8 code.
* Data: the core profile's data, rebuilt by MSH-6 on a fresh VM (same sources, same cleaning, same held-out sets).
* Dialect-only models: `--pools E` (Eastern pool only) and `--pools W` (Western pool only), same tokens as the mixed model.
* The Western ladder: nested document subsets of the Western pool (12.5 %, 25 %, 50 %, 100 % of documents, chosen by a fixed hash of
  the document index), with the PREREG mixture rule unchanged (Western share = min(0.5, 4 x Western tokens / T)).

## 2. Models (section 4 lists every run)

The core architecture, optimiser and token budget (T = 20 N). Sizes 6M, 15M (letters) and 15M, 40M (ladder). Seeds 405 and 406 for
the letters runs that the dialect comparison uses.

## 3. Measures

* bpb on every held-out set, as in PREREG (bpb_E, bpb_W, bpb_EW).
* **Five-sets share**: for the 15 stops and affricates (բ պ փ, գ կ ք, դ տ թ, ձ ծ ց, ջ ճ չ), the share of each letter's two nearest
  neighbours (cosine of input embeddings) that are in its own set, and a label-permutation p value (5,000 permutations).
* **Movement**: for each of the 39 symbols, 1 - Pearson r of its cosine row in the Eastern-only and the Western-only model, minus the
  same quantity between two seeds of one dialect (the noise floor, averaged over E and W).
* **Gap**: bpb_W - bpb_E of a model, against megabytes of Western text it trained on.

## 4. The runs (16; about 3 G4 hours of training and scoring, Estimate)

| run | what for |
|---|---|
| bpe-6M-anchor, bytes-6M-anchor | check A1: the rebuilt data reproduces core |
| letters-6M, letters-15M | L1, L2: the letters arm against bytes and bpe at equal tokens |
| letters-15M-s406 | the seed floor for the mixed model |
| letters-15M-E, letters-15M-E-s406, letters-15M-W, letters-15M-W-s406 | L4 to L6: Eastern and Western skies, and their noise floor |
| bpe-15M-W0.125, -W0.25, -W0.5, -Wfull | L7: the gap-closing curve at 15M |
| bpe-40M-W0.25, -W0.5, -Wfull | L7: the same at 40M, where the cap binds |

## 5. Forecasts (probability that the statement is true), written before any run

| # | statement | p |
|---|---|---|
| A1 | bpe-6M-anchor and bytes-6M-anchor are each within 0.005 bpb_EW of core (0.827 and 1.077) | 0.80 |
| L1 | letters beats bytes on bpb_EW at 6M and at 15M (equal tokens) | 0.90 |
| L2 | letters is worse than bpe on bpb_EW at 6M and at 15M (equal tokens; bpe from core and the anchor) | 0.90 |
| L3 | letters-15M (mixed) five-sets share is at least 0.30, with permutation p below 0.01 | 0.60 |
| L4 | the swap hunch: the mixed model's five-sets share is above both the Eastern-only and the Western-only share (seed means) | 0.45 |
| L5 | spelling, not sound: mean movement above the floor is larger for the spelling-reform letters (ւ յ է ե օ ո վ և) than for the ten sound-shift letters (բ պ գ կ դ տ ձ ծ ջ ճ) | 0.60 |
| L6 | at least 5 of the 39 symbols move by more than twice their own noise floor | 0.60 |
| L7a | at 15M the gap falls at every step of the ladder (12.5 % to 100 %) | 0.75 |
| L7b | at 40M the gap falls at every step (25 % to 100 %) | 0.70 |
| L8 | the Western-only model scores better on the Western test than the mixed model at 15M (it sees about twice the Western text) | 0.70 |
| L9 | in the mixed letters-15M model, և has ե or ւ among its three nearest neighbours | 0.50 |
| O5 | the whole letters session (data rebuild to export) stays under 5 G4 hours | 0.75 |

## 6. What would change the plan

* If A1 fails, every comparison with core numbers is dropped and only within-session comparisons are reported.
* If a run fails, it is rerun once from its checkpoint; a run that fails twice is reported as missing.
* The constellation and the gap piece are built from whatever the export holds. Their captions name the run and the grade.

## 7. Not tested here (ideas for later, not forecasts)

Sound (the letters voiced in Eastern and Western pronunciation), contributed Western texts (needs consent, licensing and the
governance group in `participation/`), Grabar letters, attention between letters, and larger letters models.
