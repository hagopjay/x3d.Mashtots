#!/usr/bin/env python3
"""The letters study (LETTERS-PREREG.md): one token per Armenian letter, dialect-only models, the Western data ladder, and the export
that the letter constellation reads.

* `letters` arm: a fixed vocabulary of single characters (the 38 letters in both cases, the ligature և, Latin letters, digits,
  punctuation, Armenian punctuation, space, newline), with byte fallback for anything else. Byte-exact by construction. Unlike the
  `bytes` arm, an Armenian letter is ONE token, not two meaningless halves.
* dialect-only training: `mp_train.py --pools E` or `--pools W` (the trainer reads only that pool).
* the Western ladder: nested document subsets W@0.125 c W@0.25 c W@0.5 c W of the Western pool, for any arm (`--w-file`).
* the export (`mashtots-letters/1`): each letters run's input embedding of the 39 symbols, their cosine matrix, the five-sets test,
  and the change between the Eastern and the Western model against the seed-to-seed noise floor.

usage: python3 -I mp_letters.py vocab  --root DATA
       python3 -I mp_letters.py ladder --root DATA --arm bpe [--fracs 0.125,0.25,0.5]
       python3 -I mp_letters.py export --root DATA --runs RUNS --out results/mashtots_letters_export.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import string
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mp_common as C  # noqa: E402

LIGATURE = C.ECH_YIWN
ARMENIAN_PUNCT = "«»՝՞՜՛։՚․…—–"
SYMBOLS_39 = list(C.LETTERS_38) + [LIGATURE]          # the constellation's 39 (upper case for the 38; the ligature has no capital)
TRIADS = {"lips": "ԲՊՓ", "back of the tongue": "ԳԿՔ", "teeth": "ԴՏԹ", "teeth, hissing": "ՁԾՑ", "palate, hushing": "ՋՃՉ"}
REFORM = set("ՒՅԷԵՕՈՎ") | {LIGATURE}                   # letters whose use the 1920s-40s spelling reform changed (Estimate)
SOUND_SHIFT = set("ԲՊԳԿԴՏՁԾՋՃ")                         # letters whose sound differs between Eastern and Western


def default_symbols():
    seen, out = set(), []
    for ch in (C.LETTERS_38 + C.LETTERS_38_LOWER + LIGATURE + string.ascii_letters + string.digits + string.punctuation + " \n"
               + ARMENIAN_PUNCT):
        if ch not in seen:
            seen.add(ch)
            out.append(ch)
    return out


class LettersEncoder:
    """encode(text) -> ids. 0 = <eos>, 1..256 = byte fallback, 257.. = one id per symbol. Same interface as mp_tok.Encoder."""

    arm = "letters"

    def __init__(self, symbols):
        self.symbols = list(symbols)
        self.eos, self.base = 0, 257
        self.vocab_size = self.base + len(self.symbols)
        cps = np.array([ord(c) for c in self.symbols], dtype=np.uint32)
        self._order = np.argsort(cps)
        self._cps = cps[self._order]
        self._sym_bytes = np.array([len(c.encode("utf-8")) for c in self.symbols], dtype=np.int64)
        self._sym_utf8 = [c.encode("utf-8") for c in self.symbols]
        self.tok = None                      # no HF tokenizer behind it (mp_export checks this attribute)

    # ---------------------------------------------------------------- io
    @classmethod
    def load(cls, root):
        d = json.loads((pathlib.Path(root) / "tokenizers" / "letters.json").read_text())
        return cls(d["symbols"])

    def save(self, root):
        p = pathlib.Path(root) / "tokenizers" / "letters.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(dict(kind="letters", version=1, eos=0, byte_fallback=[1, 256], base=self.base, symbols=self.symbols),
                                ensure_ascii=False, indent=0))
        return p

    def symbol_id(self, ch):
        return self.base + self.symbols.index(ch)

    # ---------------------------------------------------------------- the code
    def encode(self, text):
        if not text:
            return []
        cp = np.frombuffer(text.encode("utf-32-le"), dtype=np.uint32)
        pos = np.searchsorted(self._cps, cp)
        pos_c = np.minimum(pos, len(self._cps) - 1)
        found = self._cps[pos_c] == cp
        ids = self.base + self._order[pos_c]
        if found.all():
            return ids.astype(np.int64).tolist()
        out = []
        for ok, i, c in zip(found.tolist(), ids.tolist(), cp.tolist()):
            if ok:
                out.append(i)
            else:
                out.extend(1 + b for b in chr(c).encode("utf-8"))
        return out

    def encode_batch(self, texts):
        return [self.encode(t) for t in texts]

    def token_bytes(self, ids):
        a = np.asarray(ids, dtype=np.int64)
        out = np.ones(len(a), dtype=np.int64)
        m = a >= self.base
        out[m] = self._sym_bytes[a[m] - self.base]
        out[a == self.eos] = 0
        return out.tolist()

    def decode(self, ids):
        b = bytearray()
        for i in ids:
            if i >= self.base:
                b += self._sym_utf8[i - self.base]
            elif i >= 1:
                b.append(i - 1)
        return b.decode("utf-8", errors="replace")

    def roundtrip(self, texts):
        bad = 0
        for t in texts:
            ids = self.encode(t)
            if self.decode(ids) != t or sum(self.token_bytes(ids)) != len(t.encode("utf-8")):
                bad += 1
        return bad


def build_vocab(root):
    enc = LettersEncoder(default_symbols())
    p = enc.save(root)
    print(f"letters vocabulary: {len(enc.symbols)} symbols + 257 (eos, bytes) = {enc.vocab_size} ids -> {p}")
    return enc


# ------------------------------------------------------------------------------------------------ the Western ladder
def _doc_u(i):
    return int(hashlib.sha256(f"wladder:{i}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def make_w_ladder(root, arm, fracs=(0.125, 0.25, 0.5)):
    """Nested document subsets of tokens/<arm>/W.bin: a document is kept in W@f when its fixed random number is below f."""
    root = pathlib.Path(root)
    src = root / "tokens" / arm / "W.bin"
    dt = np.uint8 if arm == "bytes" else np.uint16
    eos = 255 if arm == "bytes" else _eos_id(root, arm)
    a = np.fromfile(src, dtype=dt)
    ends = np.flatnonzero(a == eos)
    starts = np.concatenate([[0], ends[:-1] + 1])
    u = np.array([_doc_u(i) for i in range(len(ends))])
    tok_bytes = _token_byte_table(root, arm)
    rep = C.load_json(root / "tokens" / "ladder_report.json", {})
    full_bytes = None
    for f in sorted(fracs) + [1.0]:
        keep = np.flatnonzero(u < f) if f < 1 else np.arange(len(ends))
        parts = [a[starts[k]:ends[k] + 1] for k in keep]
        sub = np.concatenate(parts) if parts else np.zeros(0, dtype=dt)
        nbytes = int(tok_bytes[sub.astype(np.int64)].sum()) if tok_bytes is not None else int(len(sub))
        full_bytes = nbytes if f == 1.0 else full_bytes
        name = "W.bin" if f == 1.0 else f"W@{f:g}.bin"
        if f < 1:
            sub.tofile(root / "tokens" / arm / name)
        rep[f"{arm}/{name}"] = dict(fraction=f, documents=int(len(keep)), tokens=int(len(sub)), text_mb=round(nbytes / 1e6, 3))
        print(f"  {arm} {name:<12} {len(keep):>8,} docs  {len(sub):>13,} tokens  {nbytes / 1e6:8.1f} MB of Western text")
    C.dump_json(rep, root / "tokens" / "ladder_report.json")
    return rep


def _eos_id(root, arm):
    if arm == "letters":
        return 0
    from tokenizers import Tokenizer
    return Tokenizer.from_file(str(pathlib.Path(root) / "tokenizers" / f"{arm}.json")).token_to_id("<eos>")


def _token_byte_table(root, arm):
    """Text bytes per token id (eos counts 0), so a ladder step reports megabytes of Western text, not tokens."""
    if arm == "bytes":
        t = np.ones(257, dtype=np.int64)
        t[255] = 0
        return t
    if arm == "letters":
        enc = LettersEncoder.load(root)
        return np.asarray(enc.token_bytes(list(range(enc.vocab_size))), dtype=np.int64)
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(pathlib.Path(root) / "tokenizers" / f"{arm}.json"))
    n = tok.get_vocab_size()
    t = np.zeros(n, dtype=np.int64)
    for i in range(n):
        s = tok.id_to_token(i)
        if s == "<eos>":
            t[i] = 0
        elif arm in ("bpe", "bpe_morph"):
            t[i] = len(s)                         # byte-level alphabet: one character per byte
        elif s.startswith("<0x") and len(s) == 6:
            t[i] = 1
        else:
            t[i] = len(s.encode("utf-8"))
    return t


# ------------------------------------------------------------------------------------------------ analysis
def cosine(X):
    X = np.asarray(X, dtype=np.float64)
    n = np.linalg.norm(X, axis=1, keepdims=True)
    Z = X / np.where(n > 0, n, 1)
    return Z @ Z.T


def triad_score(cos, symbols, k=2, perms=5000, seed=405):
    cos = np.asarray(cos, float)
    idx = {c: i for i, c in enumerate(symbols)}
    members = [(idx[c], s) for s in TRIADS.values() for c in s if c in idx]

    def score(M):
        hit = 0
        for i, s in members:
            order = [j for j in np.argsort(-M[i]) if j != i][:k]
            hit += sum(symbols[j] in s for j in order)
        return hit / (k * len(members))

    obs = score(cos)
    rng = np.random.default_rng(seed)
    null = np.array([score(cos[np.ix_(p, p)]) for p in (rng.permutation(len(symbols)) for _ in range(perms))])
    return dict(k=k, letters=len(members), within_share=round(float(obs), 4), chance_mean=round(float(null.mean()), 4),
                p_value=float((1 + (null >= obs).sum()) / (perms + 1)), permutations=perms)


def row_change(cos_a, cos_b):
    """Per symbol: 1 - Pearson r of its similarity row in two models (0 = same neighbourhood)."""
    a, b = np.asarray(cos_a, float), np.asarray(cos_b, float)
    n = len(a)
    out = []
    for i in range(n):
        m = np.arange(n) != i
        out.append(float(1 - np.corrcoef(a[i, m], b[i, m])[0, 1]))
    return np.asarray(out)


def _load(run_dir, device="cpu"):
    import torch
    import mp_model as M
    cfg = M.Config(**json.loads((run_dir / "config.json").read_text()))
    model = M.GPT(cfg)
    sd = torch.load(run_dir / "model.pt", map_location=device, weights_only=True)
    model.load_state_dict({k: v.float() if v.is_floating_point() else v for k, v in sd.items()})
    return model, cfg


def letter_vectors(root, run_dir):
    """The input (= tied output) embedding of the 39 symbols: lower case for the 38 letters, and the ligature."""
    enc = LettersEncoder.load(root)
    model, _ = _load(pathlib.Path(run_dir))
    W = model.emb.weight.detach().double().numpy()
    ids = [enc.symbol_id(C.LOWER[c]) for c in C.LETTERS_38] + [enc.symbol_id(LIGATURE)]
    ids_up = [enc.symbol_id(c) for c in C.LETTERS_38]
    return W[ids], W[ids_up], ids


def export(root, runs, out, seeds=(405, 406)):
    """Read every finished letters run and write the mashtots-letters/1 export, with the pre-registered tests."""
    root, runs = pathlib.Path(root), pathlib.Path(runs)
    grade = "DRY RUN (tiny model, local)" if C.LOCAL else "Measured"
    variants, meta = {}, {}
    for d in sorted(runs.glob("letters-*")):
        if not (d / "done.json").exists():
            continue
        m = json.loads((d / "meta.json").read_text())
        ev = C.load_json(d / "eval.json", {})
        pools = m.get("pools", "EW")
        key = pools + ("" if m.get("seed", 405) == seeds[0] else f"_s{m.get('seed')}")
        key = f"{key}@{m['size']}"
        X, Xu, ids = letter_vectors(root, d)
        cs = cosine(X)
        variants[key] = dict(run=d.name, size=m["size"], pools=pools, seed=m.get("seed", 405), symbols=SYMBOLS_39, cosine=cs.round(5).tolist(),
                             cosine_upper38=cosine(Xu).round(5).tolist(), triads=triad_score(cs, SYMBOLS_39),
                             bpb=dict(E=ev.get("bpb_E"), W=ev.get("bpb_W"), G=ev.get("bpb_G"), EW=ev.get("bpb_EW_equal")),
                             multiblimp={k: v["accuracy"] for k, v in ev.get("multiblimp", {}).items()},
                             note={"EW": "Eastern and Western mixed", "E": "Eastern text only", "W": "Western text only"}.get(pools, pools))
        meta[key] = m
    res = dict(schema="mashtots-letters/1", version=C.VERSION, built=C.stamp(), grade=grade,
               prereg_sha256=C.sha256_file(root / "LETTERS-PREREG.md") if (root / "LETTERS-PREREG.md").exists() else None,
               source="letters arm runs " + ", ".join(sorted(v["run"] for v in variants.values())), variants=variants, analysis={})
    A_ = res["analysis"]
    for size in sorted({v["size"] for v in variants.values()}):
        g = {k.split("@")[0]: v for k, v in variants.items() if v["size"] == size}
        if "E" in g and "W" in g:
            ch = row_change(g["E"]["cosine"], g["W"]["cosine"])
            floors = [row_change(g[a]["cosine"], g[a + f"_s{seeds[1]}"]["cosine"]) for a in ("E", "W") if a + f"_s{seeds[1]}" in g]
            floor = np.mean(floors, axis=0) if floors else None
            moved = (ch - floor) if floor is not None else None
            groups = {}
            if moved is not None:
                for name, s in (("reform", REFORM), ("sound_shift", SOUND_SHIFT)):
                    sel = [i for i, c in enumerate(SYMBOLS_39) if c in s]
                    groups[name] = round(float(moved[sel].mean()), 4)
                rest = [i for i, c in enumerate(SYMBOLS_39) if c not in REFORM and c not in SOUND_SHIFT]
                groups["other"] = round(float(moved[rest].mean()), 4)
            A_[size] = dict(symbols=SYMBOLS_39, change_E_vs_W=ch.round(4).tolist(), noise_floor=None if floor is None else floor.round(4).tolist(),
                            moved_above_floor=None if moved is None else moved.round(4).tolist(), group_means=groups,
                            triads={k: g[k]["triads"]["within_share"] for k in g})
    out = pathlib.Path(out)
    C.dump_json(res, out)
    print(f"letters export: {out} ({out.stat().st_size / 1e6:.2f} MB); variants {sorted(variants)}")
    for size, a in A_.items():
        print(f"  {size}: five-sets share by variant {a['triads']}; mean movement above the seed floor {a['group_means']}")
    return res


def ladder_table(runs, out=None):
    """The gap-closing curve: Western megabytes vs the Western minus Eastern gap, for every ladder run."""
    rows = []
    for d in sorted(pathlib.Path(runs).glob("*")):
        if not (d / "done.json").exists():
            continue
        m = json.loads((d / "meta.json").read_text())
        if not m.get("w_file") and not d.name.endswith("-Wfull"):
            continue
        ev = json.loads((d / "eval.json").read_text())
        rows.append(dict(run=d.name, arm=m["arm"], size=m["size"], w_file=m.get("w_file") or "W.bin", w_mb=m.get("w_text_mb"),
                         w_share=round(m["mixture"].get("W", 0), 4), w_epochs=m["epochs_per_pool"].get("W"),
                         bpb_E=ev.get("bpb_E"), bpb_W=ev.get("bpb_W"), gap=None if ev.get("bpb_W") is None else ev["bpb_W"] - ev["bpb_E"]))
    rows.sort(key=lambda r: (r["arm"], C.non_embedding_params(r["size"]), r["w_mb"] or 0))
    if out:
        C.dump_json(dict(grade="DRY RUN (tiny model, local)" if C.LOCAL else "Measured", rows=rows), out)
    for r in rows:
        print(f"  {r['run']:<26} W {r['w_mb'] or 0:>9.3f} MB  share {r['w_share']:.3f}  epochs {r['w_epochs']}  gap {r['gap'] if r['gap'] is None else round(r['gap'], 4)}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["vocab", "ladder", "export", "table", "selftest"])
    ap.add_argument("--root")
    ap.add_argument("--runs")
    ap.add_argument("--out")
    ap.add_argument("--arm", default="bpe")
    ap.add_argument("--fracs", default="0.125,0.25,0.5")
    a = ap.parse_args()
    if a.cmd == "vocab":
        build_vocab(a.root)
    elif a.cmd == "ladder":
        make_w_ladder(a.root, a.arm, tuple(float(x) for x in a.fracs.split(",")))
    elif a.cmd == "export":
        export(a.root, a.runs, a.out)
    elif a.cmd == "table":
        ladder_table(a.runs, a.out)
    else:
        enc = LettersEncoder(default_symbols())
        texts = ["Հայր մեր, որ յերկինս ես", "Բարեւ, աշխարհ! 123 «ու» և ֆ…", "emoji 🙂 and ç", ""]
        assert enc.roundtrip(texts) == 0
        ids = enc.encode("Մաշտոց")
        assert len(ids) == 6 and all(i >= enc.base for i in ids), ids
        assert len(enc.encode("🙂")) == 4
        print(f"letters self-test: {enc.vocab_size} ids, round trip OK, Մաշտոց = 6 tokens (bytes arm: 12)")


if __name__ == "__main__":
    main()
