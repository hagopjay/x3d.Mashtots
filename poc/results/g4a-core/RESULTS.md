# Mashtots PoC results (Measured)

Built 2026-11-15 09:56:51 UTC. Every number below is **Measured** unless its row says otherwise. Rules: `PREREG.md`.

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
| bpe | 32000 | 1.83 | 1.60 | 1.78 | 0.44 | 0.17 / 0.23 | 0.19 / 0.31 | 0 |
| mashtots | 32000 | 2.52 | 2.27 | 2.11 | 0.81 | 0.64 / 0.36 | 0.66 / 0.42 | 0 |
| bpe_morph | 32000 | 2.52 | 2.27 | 2.11 | 0.81 | 0.64 / 0.36 | 0.66 / 0.42 | 0 |
| mashtots_nomorph | 32000 | 1.83 | 1.60 | 1.78 | 0.44 | 0.18 / 0.24 | 0.20 / 0.32 | 0 |

Our tokenizers are trained on Armenian only, so their UDHR ratio says what an Armenian-first vocabulary costs English, not a like-for-like bill.

## The runs

| run | N (non-emb.) | tokens | bpb E | bpb W | bpb G | **bpb E+W** | ArmWeb test | W - E | MultiBLiMP hye / hyw | minutes |
|---|---|---|---|---|---|---|---|---|---|---|
| bpe-6M | 6.4M | 129M | 0.812 | 0.842 | 1.552 | **0.827** | 0.689 | 0.030 | 0.92 / 0.92 | 1.8 |
| bytes-6M | 6.4M | 129M | 1.062 | 1.093 | 1.947 | **1.077** | 0.947 | 0.031 | 0.81 / 0.79 | 1.0 |
| mashtots-6M | 6.4M | 129M | 0.817 | 0.848 | 1.614 | **0.833** | 0.697 | 0.031 | 0.92 / 0.91 | 1.8 |
| bpe-15M | 14.2M | 283M | 0.693 | 0.726 | 1.393 | **0.710** | 0.577 | 0.033 | 0.96 / 0.95 | 5.7 |
| bpe-15M-G | 14.2M | 283M | 0.690 | 0.724 | 1.099 | **0.707** | 0.575 | 0.034 | 0.96 / 0.96 | 5.7 |
| bytes-15M | 14.2M | 283M | 0.907 | 0.937 | 1.798 | **0.922** | 0.791 | 0.030 | 0.92 / 0.92 | 3.7 |
| mashtots-15M | 14.2M | 283M | 0.716 | 0.746 | 1.432 | **0.731** | 0.596 | 0.030 | 0.95 / 0.96 | 5.7 |
| bpe-40M | 38.5M | 771M | 0.625 | 0.669 | 1.287 | **0.647** | 0.514 | 0.045 | 0.98 / 0.97 | 26.7 |
| bpe-40M-G | 38.5M | 771M | 0.625 | 0.669 | 1.059 | **0.647** | 0.515 | 0.044 | 0.98 / 0.96 | 26.7 |
| bytes-40M | 38.5M | 771M | 0.767 | 0.800 | 1.488 | **0.783** | 0.654 | 0.032 | 0.97 / 0.95 | 20.6 |
| mashtots-40M | 38.5M | 771M | 0.644 | 0.680 | 1.329 | **0.662** | 0.533 | 0.036 | 0.97 / 0.98 | 26.7 |

## H2 Does the script-aware tokenizer help? **FAIL**

Rule: mashtots better at the largest size with both arms and worse at none. Delta = bpb(bpe) - bpb(other), E+W equal; positive = the other arm is better.

| size | mashtots vs bpe | 95 % CI | verdict | bytes vs bpe | 95 % CI |
|---|---|---|---|---|---|
| 6M | -0.0060 | [-0.0078, -0.0042] | worse | -0.2505 | [-0.2561, -0.2444] |
| 15M | -0.0213 | [-0.0224, -0.0201] | worse | -0.2123 | [-0.2168, -0.2073] |
| 40M | -0.0151 | [-0.0164, -0.0136] | worse | -0.1363 | [-0.1396, -0.1332] |

## H3 The floor, against the deck's bpb(N) = 4.9e5 N^-0.795 + 0.439

| arm | N | ours (ArmWeb test) | deck | gap | deck's grade at N | verdict |
|---|---|---|---|---|---|---|
| bytes | 6.4M | 0.947 | 2.335 | -59.4 % | Estimate (outside 70M-1B) | outside the deck's range |
| bytes | 14.2M | 0.791 | 1.451 | -45.5 % | Estimate (outside 70M-1B) | outside the deck's range |
| bytes | 38.5M | 0.654 | 0.895 | -26.9 % | Estimate (outside 70M-1B) | outside the deck's range |
| bpe | 6.4M | 0.689 | 2.335 | -70.5 % | Estimate (outside 70M-1B) | outside the deck's range |
| bpe | 14.2M | 0.577 | 1.451 | -60.2 % | Estimate (outside 70M-1B) | outside the deck's range |
| bpe | 38.5M | 0.514 | 0.895 | -42.5 % | Estimate (outside 70M-1B) | outside the deck's range |
| mashtots | 6.4M | 0.697 | 2.335 | -70.1 % | Estimate (outside 70M-1B) | outside the deck's range |
| mashtots | 14.2M | 0.596 | 1.451 | -58.9 % | Estimate (outside 70M-1B) | outside the deck's range |
| mashtots | 38.5M | 0.533 | 0.895 | -40.4 % | Estimate (outside 70M-1B) | outside the deck's range |

## H4 Does Grabar text help Grabar? **PASS**

* 15M: Delta bpb_G = 0.2939 (95 % CI [0.2612, 0.3188]), better; cost on E+W -0.0028 bpb
* 40M: Delta bpb_G = 0.2287 (95 % CI [0.1949, 0.256]), better; cost on E+W +0.0003 bpb

The `-G` models were trained on CC BY-NC-SA text (UD CAVaL): they carry a non-commercial condition.

## H6 Grammar (MultiBLiMP)

* bytes 40M, hye: 0.969 of 1415 pairs (one-sided p = 0 against chance)
* bytes 40M, hyw: 0.954 of 1153 pairs (one-sided p = 1.1e-255 against chance)
* bpe 40M, hye: 0.977 of 1415 pairs (one-sided p = 0 against chance)
* bpe 40M, hyw: 0.968 of 1153 pairs (one-sided p = 0 against chance)
* mashtots 40M, hye: 0.972 of 1415 pairs (one-sided p = 0 against chance)
* mashtots 40M, hyw: 0.977 of 1153 pairs (one-sided p = 0 against chance)

## Data (Measured on this run's download)

| pool | MB | documents |
|---|---|---|
| E | 3519.3 | 1382477 |
| W | 724.5 | 148662 |
| G | 1.2 | 284 |

Variety classifier on single UD test sentences: {'E': 0.9901, 'W': 0.9924, 'G': 1.0}.
Dialect x spelling, bytes kept: ?|classical 0.2 MB, ?|unclear 0.2 MB, E|classical 32.3 MB, E|reformed 3307.2 MB, E|unclear 179.3 MB, G|classical 1.2 MB, G|unclear 0.0 MB, W|classical 723.2 MB, W|reformed 0.6 MB, W|unclear 0.6 MB

## Grades of the deck's figures used here

* token_bill_udhr_hy_over_en: Measured (deck)
* word_shapes: Measured (deck)
* data_law: Established (published fit); its plotted points are placeholders
* armenian_floor: Established within 70M-1B parameters, Estimate beyond
* closing: Conjecture
