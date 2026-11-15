# Reading the core run (run g4a, profile core, 15 Nov 2026)

The core profile trained 11 models on the shared Colab G4, from 07:48 to 09:55 UTC: 3 arms at 6M, 15M and 40M, plus bpe-G at 15M and 40M.
`RESULTS.md` was copied from `MyDrive/x3dlab/mashtots/runs/g4a-core/results/`. Numbers are Measured unless marked otherwise.

## Verdicts (as pre-registered)

| hypothesis | verdict | the numbers |
|---|---|---|
| H1 token tax | reproduces the deck | all six big-lab tokenizers within 5 % (smoke and core agree) |
| H2 script-aware tokenizer helps | **FAIL** | mashtots is worse than bpe at every size: -0.006, -0.021 and -0.015 bpb_EW at 6M, 15M and 40M; every CI is below 0 |
| H3 floor vs the deck | points only (core has 3 sizes; no fit) | see "H3 needs a deviation" below |
| H4 Grabar helps Grabar | **PASS** | bpb_G -0.294 at 15M and -0.229 at 40M (both CIs above 0); E+W cost -0.003 and +0.0003 |
| H5 Western gap | descriptive | bpe 0.030, 0.033, 0.045; mashtots 0.031, 0.030, 0.036 |
| H6 grammar | far above chance | 40M: bpe 0.977 / 0.968, mashtots 0.972 / **0.977**, bytes 0.969 / 0.954 (hye / hyw) |

## What it means

1. **The smoke gap was an artifact of tiny data.** At 6M, mashtots trailed by 0.278 bpb in smoke (20M tokens on 0.11 GB) and by 0.006 in core (129M tokens on 4.2 GB).
2. **mashtots loses at equal compute, but narrowly.** It reads about a third less text per token, yet trails by only 1.5 % to 3 %. An equal-bytes comparison is the natural exploratory follow-up. PREDICTIONS.md already named it.
3. **Western Armenian is data-starved, and the cap shows it.** The Western pool (0.72 GB) is a fifth the size of the Eastern one. At 40M, bpe hit the 4-epoch cap on Western: its Western share fell from 50 % to 43.8 % and it saw each Western token 4.0 times (meta.json). Its Western gap widened from 0.033 to 0.045. mashtots and bytes read less text per token, so they stayed under the cap (50 %, 3.1 and 0.5 epochs).
   *Correction, 15 Nov 10:30 UTC:* an earlier version of this note said mashtots helps Western Armenian. At 40M that comparison is confounded, because only bpe had its Western share cut. At 15M, where both arms had 50 %, mashtots' Western gap is smaller by 0.003, with no CI computed. So "mashtots helps Western" is unresolved, not Suspected. A clean test needs equal Western share and several seeds.
4. **Grabar text is nearly free and very effective.** Gospel text was 0.29 % of training at 15M and 0.11 % at 40M (meta.json; an earlier version said about 1 %), each token seen 4 times. It cut Grabar bpb by 0.29 and 0.23 with no cost to E+W. Note the CC BY-NC-SA condition on the -G models.
5. **The scaling is smooth.** bpe bpb_EW goes 0.827, 0.710, 0.647 for 6.4M, 14.2M and 38.5M non-embedding parameters.

## H3 needs a deviation (proposed here, dated 15 Nov 2026, before any full run)

The deck's curve `4.9e5 N^-0.795 + 0.439` comes from COPA-AI, "From Zero to Hero: An Open LLM Ecosystem for Armenian" (arXiv 2609.03350), equation 1.
It is fitted on **mean panel bpb**: the average of six sets (ArmWeb iid, ArmWeb tail, FineWeb-2 test, hyWiki, LR-Sum, FLORES), at 70M to 1B parameters.
PREREG H3 compares our `E_armweb_test` alone with that curve. ArmWeb news is the easiest member of the panel. In the paper's own Table 3, at 410M,
ArmWeb-iid is about 0.42 while the panel mean is about 0.53. So H3 as written compares unlike quantities, and its "better / consistent / worse" verdicts would be misleading.

Proposed deviation, to be adopted before `full` runs and reported as a deviation everywhere it is used:
* keep the pre-registered H3 table unchanged (it is reported, never deleted);
* add H3b, which compares our `E_armweb_test` with COPA's own ArmWeb-iid numbers at matched N, and our mean over the sets we share with their panel (FineWeb-2 test and Wikipedia) with their per-set columns;
* conclusions about the deck come only from H3b, and are labelled "deviation from PREREG, adopted 15 Nov 2026 before the full run".

## Forecasts settled by core (PREDICTIONS.md, written 28 Oct)

| # | forecast | p | outcome | Brier |
|---|---|---|---|---|
| L1 | H2 PASS | 0.25 | no | 0.06 |
| L2 | bytes worse than bpe at every size | 0.90 | yes | 0.01 |
| L3 | at 6M every arm's ArmWeb bpb below the deck's 2.44 | 0.95 | yes | 0.00 |
| L5 | bpe 40M ArmWeb bpb between 0.70 and 1.00 | 0.55 | **no** (0.514) | 0.30 |
| L6 | Western gap positive for every bpe run of 40M and above | 0.70 | yes so far (0.045; full adds 85M and 150M) | 0.09 |
| L7 | H4 PASS | 0.75 | yes | 0.06 |
| L8 | largest bpe MultiBLiMP above 0.60 (hye) / (hyw) | 0.60 / 0.50 | yes / yes (0.977 / 0.968; provisional until full) | 0.16 / 0.25 |
| O3 | core training time within 30 % of the projection | 0.65 | yes (2.1 h vs 2.65 h projected) | 0.12 |

Mean Brier over these nine: 0.118, with smoke's six at 0.17. The worst calls were L5 and L8: I underestimated how good small Armenian models get on news.

## Cost

Training 2.1 h; the session from MSH-4 to MSH-14 took about 2.3 h of G4 time, about 20 units at 8.7 units per hour (Estimate).
