# Mashtots PoC results (Measured)

Built 2026-11-15 07:31:55 UTC. Every number below is **Measured** unless its row says otherwise. Rules: `PREREG.md`.

## H1 The token bill (UDHR, Armenian tokens / English tokens)

| tokenizer | ours | deck (its grade: Measured) | gap | within 5 % |
|---|---|---|---|---|
| o200k (GPT-4o, gpt-oss) | 1.52 | 1.51 | +0.7 % | yes |
| Mistral Tekken (= Nemotron Nano 9B v2, Nemotron 3 Nano) | 1.76 | 1.74 | +1.1 % | yes |
| Gemma 3 | 2.80 | 2.67 | +4.9 % | yes |
| DeepSeek V3 | 2.94 | 2.87 | +2.4 % | yes |
| Qwen 2.5 | 5.63 | 5.41 | +4.1 % | yes |
| cl100k (GPT-4) | 10.54 | 10.15 | +3.8 % | yes |

## Our tokenizers (tokens per word on UD test sentences; stem-boundary recall / precision against UD lemmas)

| arm | vocab | Eastern | Western | Grabar | UDHR hy/en | boundary E (R/P) | boundary W (R/P) | round-trip failures |
|---|---|---|---|---|---|---|---|---|
| bytes | 257 | 14.15 | 12.92 | 10.31 | 1.95 | 1.00 / 0.06 | 1.00 / 0.07 | 0 |
| bpe | 32000 | 1.84 | 1.66 | 1.79 | 0.44 | 0.19 / 0.24 | 0.21 / 0.30 | 0 |
| mashtots | 32000 | 2.53 | 2.30 | 2.11 | 0.81 | 0.64 / 0.36 | 0.66 / 0.41 | 0 |
| bpe_morph | 32000 | 2.53 | 2.30 | 2.11 | 0.81 | 0.64 / 0.36 | 0.66 / 0.42 | 0 |
| mashtots_nomorph | 32000 | 1.84 | 1.66 | 1.79 | 0.44 | 0.19 / 0.24 | 0.22 / 0.32 | 0 |

Our tokenizers are trained on Armenian only, so their UDHR ratio says what an Armenian-first vocabulary costs English, not a like-for-like bill.

## The runs

| run | N (non-emb.) | tokens | bpb E | bpb W | bpb G | **bpb E+W** | ArmWeb test | W - E | MultiBLiMP hye / hyw | minutes |
|---|---|---|---|---|---|---|---|---|---|---|
| bpe-6M | 6.4M | 20M | 1.197 | 1.284 | 2.062 | **1.241** | 1.084 | 0.086 | 0.73 / 0.72 | 0.3 |
| bytes-6M | 6.4M | 20M | 2.051 | 2.098 | 2.293 | **2.075** | 2.033 | 0.048 | 0.65 / 0.59 | 0.2 |
| mashtots-6M | 6.4M | 20M | 1.471 | 1.566 | 2.243 | **1.519** | 1.379 | 0.095 | 0.69 / 0.65 | 0.3 |

## H2 Does the script-aware tokenizer help? **FAIL**

Rule: mashtots better at the largest size with both arms and worse at none. Delta = bpb(bpe) - bpb(other), E+W equal; positive = the other arm is better.

| size | mashtots vs bpe | 95 % CI | verdict | bytes vs bpe | 95 % CI |
|---|---|---|---|---|---|
| 6M | -0.2783 | [-0.2833, -0.2739] | worse | -0.8341 | [-0.8591, -0.8114] |

## H3 The floor, against the deck's bpb(N) = 4.9e5 N^-0.795 + 0.439

| arm | N | ours (ArmWeb test) | deck | gap | deck's grade at N | verdict |
|---|---|---|---|---|---|---|
| bytes | 6.4M | 2.033 | 2.335 | -12.9 % | Estimate (outside 70M-1B) | outside the deck's range |
| bpe | 6.4M | 1.084 | 2.335 | -53.6 % | Estimate (outside 70M-1B) | outside the deck's range |
| mashtots | 6.4M | 1.379 | 2.335 | -40.9 % | Estimate (outside 70M-1B) | outside the deck's range |

## H4 Does Grabar text help Grabar? **not run**


The `-G` models were trained on CC BY-NC-SA text (UD CAVaL): they carry a non-commercial condition.

## H6 Grammar (MultiBLiMP)

* bytes 6M, hye: 0.654 of 1415 pairs (one-sided p = 7.6e-32 against chance)
* bytes 6M, hyw: 0.590 of 1153 pairs (one-sided p = 5.9e-10 against chance)
* bpe 6M, hye: 0.730 of 1415 pairs (one-sided p = 1.1e-69 against chance)
* bpe 6M, hyw: 0.717 of 1153 pairs (one-sided p = 5.6e-51 against chance)
* mashtots 6M, hye: 0.688 of 1415 pairs (one-sided p = 8.5e-47 against chance)
* mashtots 6M, hyw: 0.655 of 1153 pairs (one-sided p = 2.1e-26 against chance)

## Data (Measured on this run's download)

| pool | MB | documents |
|---|---|---|
| E | 45.4 | 18191 |
| W | 43.1 | 9705 |
| G | 0.4 | 71 |

Variety classifier on single UD test sentences: {'E': 0.9901, 'W': 0.9924, 'G': 1.0}.
Dialect x spelling, bytes kept: E|classical 0.3 MB, E|reformed 41.6 MB, E|unclear 3.5 MB, G|classical 0.4 MB, W|classical 43.1 MB, W|reformed 0.0 MB, W|unclear 0.1 MB

## Grades of the deck's figures used here

* token_bill_udhr_hy_over_en: Measured (deck)
* word_shapes: Measured (deck)
* data_law: Established (published fit); its plotted points are placeholders
* armenian_floor: Established within 70M-1B parameters, Estimate beyond
* closing: Conjecture
