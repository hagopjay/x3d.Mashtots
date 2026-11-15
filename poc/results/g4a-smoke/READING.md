# Reading the first G4 run (smoke, run g4a, 15 Nov 2026)

The G4 ran MSH-0 to MSH-14 at 07:32:47 UTC with no errors and a clean shared-kernel audit. The files beside this one were copied from
`MyDrive/x3dlab/mashtots/runs/g4a-smoke/`. Every number below is Measured on this run unless it is marked otherwise.

**What smoke is for.** PLAN.md defines smoke as "does everything run on the G4, and how fast", using 3 arms at 6M and 20M tokens each on 0.11 GB of tier-0 data.
The pre-registered verdicts come from `core` (6M, 15M and 40M at T = 20 N tokens) and `full`. The H2 "FAIL" that `mp_analyze` prints here applies its rule to the
only size smoke trains. It is an early signal, not the H2 verdict.

## What the smoke run says

| finding | numbers | grade |
|---|---|---|
| The token bill reproduces the deck for all six big-lab tokenizers | all within 5 % (o200k 1.52 vs 1.51, cl100k 10.54 vs 10.15) | Measured |
| At equal tokens, `mashtots` is clearly behind `bpe` at 6M | bpb_EW 1.519 vs 1.241; delta -0.278, 95 % CI [-0.283, -0.274] | Measured, smoke only |
| Part of that gap is text seen, as PREDICTIONS.md reason 1 expected | in the same 20M tokens, `mashtots` read 1.31 epochs of the Eastern pool and `bpe` read 1.99, about 34 % less text | Measured; how much of the 0.278 it explains is not measured |
| The `mashtots` tokenizer's whole effect is its morpheme pre-split | `mashtots` = `bpe_morph` and `mashtots_nomorph` = `bpe` on every tokenizer measure (tokens/word, boundary R/P within 0.02) | Measured |
| `bytes` loses badly at equal tokens | bpb_EW 2.075; it read 0.22 epochs, about 11 % of the text `bpe` read | Measured |
| Grammar follows bpb | MultiBLiMP hye / hyw: bpe 0.73 / 0.72, mashtots 0.69 / 0.65, bytes 0.65 / 0.59; all far above chance | Measured |
| Western is harder than Eastern for every arm | W - E: bpe 0.086, mashtots 0.095, bytes 0.048 | Measured (descriptive, H5) |
| The deck's curve says nothing at 6M | deck 2.33 at 6.4M, ours 1.08 (bpe) on ArmWeb test; the deck is an Estimate below 70M, so no conclusion (PREREG H3) | Measured vs Estimate |
| Speed | 3 runs x 20M tokens trained in 69.5 s of MSH-11, compiled | Measured |

## Forecast check so far (PREDICTIONS.md, written 28 Oct before any G4 run)

Only forecasts that this run settles are scored. Brier = (probability - outcome)^2.

| # | forecast | p | outcome | Brier | note |
|---|---|---|---|---|---|
| O2 | smoke runs to DONE without a fix | 0.55 | yes | 0.20 | |
| D1 | at least 70 % of FineWeb-2 hyw test docs classified Western | 0.60 | yes (1,464 of 1,466) | 0.16 | |
| T1 | `mashtots` spends more tokens per Eastern word | 0.70 | yes (2.53 vs 1.84) | 0.09 | |
| T2 | `mashtots` stem recall beats `bpe` by 0.10 on E and on W | 0.85 | yes (0.64 vs 0.19; 0.66 vs 0.21) | 0.02 | |
| D2 | 0.1 % to 3 % of ArmWeb bytes classified Western | 0.65 | yes (0.23 %) | 0.12 | provisional: smoke uses the ArmWeb validation split |
| D3 | decontamination removes under 2 % of Eastern web docs | 0.70 | **no** (952 of 19,372 = 4.9 %) | 0.49 | provisional: same split caveat; core decides |

Still open: O1 (the doctor's first-try ALL GOOD; he reported no errors), T3 (first merge `ու`; the sandbox rehearsal on the same data said yes), L1 to L9, O3, O4, X1.

## What this changes

Nothing in PREREG.md. The equal-tokens design stays, and core gives the verdict. The one follow-up PREDICTIONS.md already names ("run the same comparison at equal
bytes to separate the two effects") becomes worth doing if core confirms the gap. It would be an exploratory run, written down before it runs, and never part of the H2 scoring.
