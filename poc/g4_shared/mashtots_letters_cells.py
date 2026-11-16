# Mashtots LETTERS study (build v1.2) as extra cells for the SHARED Colab G4 kernel. They come AFTER the Mashtots core cells MSH-0 .. MSH-9.
# Paste each "# %%" block as its own cell and run top to bottom. Written 16 Nov 2026 by Claude for hagopjay.
# Source: github.com/hagopjay/x3d.Mashtots poc/ (branch claude/project-thread-c75a5a). The plan is poc/LETTERS-PREREG.md (exploratory).
#
# WHAT IT MAKES
#   * a letters arm (one token per Armenian letter), trained mixed, Eastern-only and Western-only, with a second seed for the noise floor;
#   * the Western ladder (bpe models on 1/8, 1/4, 1/2 and all of the Western documents) for the gap-closing piece;
#   * two private pages: the Letter Constellation (Eastern and Western skies, morph, which letters moved) and Two Shores (the gap closing).
#
# HOW TO RUN A LETTERS SESSION ON A FRESH VM (everything resumes from Drive if Colab takes the GPU back)
#   1. MSH-0 .. MSH-9 from mashtots_g4_cells.py with MSH_PROFILE = "core" (they rebuild the data and tokenizers; MSH-7, the token bill,
#      can be skipped). Do NOT run MSH-10 .. MSH-14: those train and score the core grid, which is finished (run g4a).
#   2. LTR-1 .. LTR-8 below.
#
#   cell                              where  time on the G4 (E = Estimate, M = Measured on the sandbox CPU dry run)          VRAM
#   LTR-1  configuration (form)       -      instant                                                                      0
#   LTR-2  letters tokens + ladder    CPU    ~3-6 min E (encode 4 GB of pools as letters; cut the Western ladder)         0
#   LTR-3  FREEZE the letters plan    CPU    instant (sha256 of LETTERS-PREREG.md and the code, before any letters run)    0
#   LTR-4  cost bench + projection    GPU    ~3-5 min E (letters 6M/15M, bpe/bytes 6M, bpe 15M/40M)                         ~8-20 GB E
#   LTR-5  train the 16 runs          GPU    ~2.5-3.5 h E (MSH_LTR_MAX_HOURS stops cleanly; rerun to resume)               ~8-30 GB E
#   LTR-6  export + ladder table      GPU    ~1-2 min E                                                                    <2 GB E
#   LTR-7  build the two pages        CPU    ~20 s (constellation + Two Shores, zipped)                                    0
#   LTR-8  package to Drive + audit   CPU    ~10 s                                                                         0
#
# BUDGET (Estimate, at 8.7 compute units per G4 hour): data rebuild ~0.5 h + LTR ~3-3.5 h = about 4 h, about 35 units. LTR-4 prints the
# projection from measured speed before anything long starts. The pre-registered forecast O5 is "the whole session stays under 5 G4 hours".
#
# THE SAME RULES AS THE CORE CELLS: the only new globals are MSH_LTR_* form fields; work runs inside _ltr (deleted at the end of each cell);
# every GPU cell calls MSH.gpu_guard(); nothing is written outside /content/mashtots and MyDrive/x3dlab/mashtots.

# %%
#@title LTR-1 · Letters configuration (form; instant). Needs MSH-0 .. MSH-9 first.
MSH_LTR_RUN_NAME = "ltr1"  #@param {type:"string"}
MSH_LTR_LADDER = True  #@param {type:"boolean"}
MSH_LTR_ANCHORS = True  #@param {type:"boolean"}
MSH_LTR_SIZES_OVERRIDE = ""  #@param {type:"string"}
MSH_LTR_MAX_HOURS = 0.0  #@param {type:"number"}
def _ltr():
    import pathlib
    assert getattr(MSH, "FROZEN", None) is not None or (MSH.DATA / "PREREG.sha256").exists(), "run MSH-0 .. MSH-9 first"
    MSH.LTR = pathlib.Path(MSH.DATA) / "letters"
    MSH.LTR_RUNS = MSH.LTR / "runs"
    for d in (MSH.LTR, MSH.LTR_RUNS):
        d.mkdir(parents=True, exist_ok=True)
    MSH.LTR_DRIVE = f"{MSH.DRIVE_DIR}/letters/{MSH_LTR_RUN_NAME}" if MSH.IN_COLAB else None
    MSH.LTR_DRIVE_RUNS = f"{MSH.LTR_DRIVE}/runs" if MSH.LTR_DRIVE else None
    MSH.LTR_SPECS = MSH.H.letters_grid(MSH_LTR_SIZES_OVERRIDE, ladder=MSH_LTR_LADDER, anchors=MSH_LTR_ANCHORS)
    print(f"letters study | run {MSH_LTR_RUN_NAME} | data {MSH.DATA} | letters folder {MSH.LTR} | Drive {MSH.LTR_DRIVE}")
    print(f"{len(MSH.LTR_SPECS)} runs, cheapest first:")
    for s in MSH.LTR_SPECS:
        print(f"  {s['id']:<26} {s['arm']:<8} {s['size']:>5} {s['tokens'] / 1e6:>8.0f}M tokens  {' '.join(map(str, s['args']))}")
_ltr(); del _ltr

# %%
#@title LTR-2 · Letters tokens and the Western ladder (CPU, ~3-6 min). Needs the pools (MSH-6) and the bpe tokenizer (MSH-8).
def _ltr():
    import sys, time, json
    t0 = time.time()
    src, data = str(MSH.SRC), str(MSH.DATA)
    MSH.H.sh([sys.executable, f"{src}/mp_letters.py", "selftest"])
    MSH.H.sh([sys.executable, f"{src}/mp_letters.py", "vocab", "--root", data])
    MSH.H.sh([sys.executable, f"{src}/mp_tok.py", "encode", "--root", data, "--arms", "letters", "--workers", str(MSH.WORKERS)])
    if MSH_LTR_LADDER:
        MSH.H.sh([sys.executable, f"{src}/mp_letters.py", "ladder", "--root", data, "--arm", "bpe"])
    rep = json.loads((MSH.DATA / "tokens" / "encode_report.json").read_text())
    for k in ("letters/E", "letters/W", "letters/G", "bpe/W", "bytes/W"):
        if k in rep:
            print(f"  {k:<10} {rep[k]['tokens']:>14,} tokens  {rep[k]['bytes_per_token']:.2f} bytes/token")
    print(f"LTR-2 wall time {time.time() - t0:.0f} s")
    MSH.H.checkpoint(MSH.DATA, MSH.LTR_DRIVE, ["tokens/encode_report.json", "tokens/ladder_report.json", "tokenizers/letters.json"])
_ltr(); del _ltr

# %%
#@title LTR-3 · FREEZE the letters plan and the code before any letters model trains (instant)
def _ltr():
    import json, shutil, hashlib
    names = ["LETTERS-PREREG.md", "mp_letters.py", "mp_train.py", "mp_tok.py", "mp_common.py", "mp_eval.py", "mp_model.py", "nb_helpers.py",
             "letters/alphabet.py", "letters/constellation.py", "letters/constellation_page.py", "letters/gap.py"]
    h = {n: hashlib.sha256((MSH.SRC / n).read_bytes()).hexdigest() for n in names}
    shutil.copy(MSH.SRC / "LETTERS-PREREG.md", MSH.DATA / "LETTERS-PREREG.md")       # the export records this file's sha256
    p = MSH.DATA / "LETTERS-PREREG.sha256"
    if p.exists():
        old = json.loads(p.read_text())
        if old["sha256"] != h:
            diff = sorted(n for n in h if old["sha256"].get(n) != h[n])
            raise SystemExit(f"the letters plan or code changed since it was frozen ({diff}); stop and tell Claude")
        print("already frozen at", old["frozen"], "and unchanged")
    else:
        import time
        p.write_text(json.dumps(dict(frozen=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), run=MSH_LTR_RUN_NAME, sha256=h,
                                     hardware=MSH.HWCARD["gpu"], build="v1.2-letters"), indent=1))
        print("frozen:", p)
    for n, v in h.items():
        print(f"  {v[:12]}  {n}")
    MSH.H.checkpoint(MSH.DATA, MSH.LTR_DRIVE, ["LETTERS-PREREG.md", "LETTERS-PREREG.sha256"])
_ltr(); del _ltr

# %%
#@title LTR-4 · What will the letters runs cost? Measured throughput per (arm, size), then the projection (GPU, ~3-5 min)
def _ltr():
    MSH.gpu_guard(need_gb=30 if MSH_COMPILE else 45)
    MSH.LTR_BENCH = MSH.H.bench(MSH.SRC, MSH.DATA, MSH.LTR_SPECS, compile_=MSH_COMPILE)
    print(f"\n{'arm':<10}{'size':>6}{'tok/s':>12}{'peak VRAM GB':>14}   (Measured on {MSH.HWCARD['gpu'][0]})")
    for (arm, size), b in sorted(MSH.LTR_BENCH.items(), key=lambda kv: (MSH.H.C.non_embedding_params(kv[0][1]), kv[0][0])):
        pk = b.get("peak_mem_gb")
        print(f"{arm:<10}{size:>6}{b['tok_per_s']:>12,.0f}{(pk if pk is not None else float('nan')):>14.1f}")
    MSH.LTR_PLAN_ROWS, MSH.LTR_PLAN_HOURS = MSH.H.project(MSH.LTR_SPECS, MSH.LTR_BENCH, MSH_UNITS_PER_HOUR)
    MSH.H.checkpoint(MSH.DATA, MSH.LTR_DRIVE, ["bench"])
_ltr(); del _ltr

# %%
#@title LTR-5 · Train the letters runs, cheapest first (GPU; resume-safe, checkpoints to Drive every 15 min, finished runs skipped)
def _ltr():
    import json, time
    MSH.gpu_guard(need_gb=30 if MSH_COMPILE else 45)
    assert (MSH.DATA / "LETTERS-PREREG.sha256").exists(), "run LTR-3 (Freeze) first"
    t0, before = time.time(), sorted(p.parent.name for p in MSH.LTR_RUNS.glob("*/done.json"))
    try:
        MSH.LTR_DONE, MSH.LTR_LEFT = MSH.H.train_grid(MSH.SRC, MSH.DATA, MSH.LTR_SPECS, MSH.LTR_RUNS, MSH.LTR_DRIVE_RUNS,
                                                      max_hours=MSH_LTR_MAX_HOURS, compile_=MSH_COMPILE)
        status = "ok"
    except BaseException as exc:
        status = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        rec = dict(start=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)), seconds=round(time.time() - t0, 1), status=status,
                   finished_before=before, finished_after=sorted(p.parent.name for p in MSH.LTR_RUNS.glob("*/done.json")),
                   compile=MSH_COMPILE, max_hours=MSH_LTR_MAX_HOURS, gpu=MSH.HWCARD["gpu"][0])
        with open(MSH.LTR / "train_wall.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"LTR-5 session: {rec['seconds'] / 3600:.2f} h, {status}; logged to letters/train_wall.jsonl")
        MSH.H.checkpoint(MSH.LTR, MSH.LTR_DRIVE, ["train_wall.jsonl"])
_ltr(); del _ltr

# %%
#@title LTR-6 · Export the letters models and the ladder table (GPU or CPU, ~1-2 min)
def _ltr():
    import sys, json
    src = str(MSH.SRC)
    MSH.H.sh([sys.executable, f"{src}/mp_letters.py", "export", "--root", str(MSH.DATA), "--runs", str(MSH.LTR_RUNS),
              "--out", str(MSH.LTR / "letters_export.json")])
    MSH.H.sh([sys.executable, f"{src}/mp_letters.py", "table", "--runs", str(MSH.LTR_RUNS), "--out", str(MSH.LTR / "ladder_table.json")])
    # the anchors against core (check A1): core's 6M numbers from the frozen g4a run
    core = {"bpe-6M": 0.827, "bytes-6M": 1.077}
    for rid, ref in core.items():
        p = MSH.LTR_RUNS / f"{rid}-anchor" / "eval.json"
        if p.exists():
            v = json.loads(p.read_text()).get("bpb_EW_equal")
            print(f"  A1 {rid}-anchor: bpb_EW {v:.4f} vs core {ref} -> {'within' if abs(v - ref) <= 0.005 else 'OUTSIDE'} 0.005")
    MSH.H.checkpoint(MSH.LTR, MSH.LTR_DRIVE, ["letters_export.json", "ladder_table.json"])
_ltr(); del _ltr

# %%
#@title LTR-7 · Build the two private pages: Letter Constellation and Two Shores (CPU, ~20 s), zipped for download
def _ltr():
    import sys, shutil
    src = str(MSH.SRC)
    sky, gap = MSH.LTR / "pages" / "constellation", MSH.LTR / "pages" / "two_shores"
    MSH.H.sh([sys.executable, f"{src}/letters/constellation.py", "--export", str(MSH.LTR / "letters_export.json"), "--out", str(sky)])
    if (MSH.LTR / "ladder_table.json").exists() and MSH_LTR_LADDER:
        MSH.H.sh([sys.executable, f"{src}/letters/gap.py", "--table", str(MSH.LTR / "ladder_table.json"), "--out", str(gap)])
    z = shutil.make_archive(str(MSH.LTR / f"letters_pages_{MSH_LTR_RUN_NAME}"), "zip", MSH.LTR / "pages")
    print("pages:", sky, gap, "\nzip:", z, "(private: give it to Claude, who checks it and publishes a private preview)")
    MSH.H.checkpoint(MSH.LTR, MSH.LTR_DRIVE, ["pages", f"letters_pages_{MSH_LTR_RUN_NAME}.zip"])
_ltr(); del _ltr

# %%
#@title LTR-8 · Package to Drive, then audit the shared kernel (CPU, ~10 s)
def _ltr():
    import os, sys, json, time, hashlib
    wall = [json.loads(x) for x in open(MSH.LTR / "train_wall.jsonl")] if (MSH.LTR / "train_wall.jsonl").exists() else []
    info = dict(version="mashtots-poc v1.2 letters", run=MSH_LTR_RUN_NAME, finished=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                hardware=MSH.HWCARD, runs_done=sorted(p.parent.name for p in MSH.LTR_RUNS.glob("*/done.json")),
                runs_planned=[s["id"] for s in MSH.LTR_SPECS], projected_hours=round(getattr(MSH, "LTR_PLAN_HOURS", 0.0), 2),
                train_wall_hours=round(sum(r["seconds"] for r in wall) / 3600, 3), units_per_hour=MSH_UNITS_PER_HOUR)
    (MSH.LTR / "run_info.json").write_text(json.dumps(info, indent=1))
    MSH.H.checkpoint(MSH.LTR, MSH.LTR_DRIVE, ["run_info.json"])
    print(json.dumps(info, indent=1))
    g, snap = globals(), MSH.SNAP
    changed = [k for k, i in snap["globals"].items() if k in g and id(g[k]) != i and k != "MSH" and not k.startswith("MSH_")]
    new = sorted(k for k in g if not k.startswith("_") and k not in snap["globals"] and k != "MSH" and not k.startswith("MSH_"))
    env_same = hashlib.sha256(json.dumps(sorted(os.environ.items())).encode()).hexdigest() == snap["env"]
    print("\nKERNEL AUDIT (since MSH-0): globals rebound:", changed or "none", "| new globals:", new or "none",
          "| sys.path added:", [p for p in sys.path if p not in snap["path"]] or "none", "| os.environ unchanged:", env_same)
    print("DONE. Letters results:", MSH.LTR_DRIVE or MSH.LTR)
_ltr(); del _ltr
