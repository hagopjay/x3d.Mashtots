# Mashtots PoC (build v1.2, shared-kernel edition; v1.2 adds the letters study, see mashtots_letters_cells.py) as extra cells for the SHARED Colab G4 kernel (the Unreal lane's notebook 07).
# Paste each "# %%" block as its own cell, at the end of the notebook, and run them top to bottom: MSH-0 first, then in order.
# Hardware these numbers are for: Colab G4 = NVIDIA RTX PRO 6000 Blackwell Server Edition, 96 GB, driver 580.82.07, 48 CPUs, 177 GB RAM.
# Written 15 Nov 2026 by Claude for hagopjay. Source: github.com/hagopjay/x3d.Mashtots poc/ (branch claude/project-thread-c75a5a).
#
# HOW THIS STAYS OUT OF THE UNREAL LANE'S WAY
#  * The only globals these cells create are MSH (one namespace) and the MSH_* form fields. Each cell's work runs inside a function
#    called _msh, which is deleted at the end of the cell, so no loop variable or import leaks into the kernel.
#  * Nothing is pip-installed into the kernel. Missing packages go into /content/mashtots/pydeps with --no-deps, and only the
#    subprocesses see that folder. numpy, Pillow and torch are never installed. The kernel's os.environ and sys.path are left alone,
#    except that one folder (/content/mashtots/src) is APPENDED to sys.path.
#  * Every torch job runs as a foreground subprocess, so the cells queue behind the Unreal cells (Colab runs one cell at a time).
#  * Every GPU cell starts with MSH.gpu_guard(): it stops if nvidia-smi shows an Unreal process (UnrealEditor, UnrealBuildTool,
#    ShaderCompileWorker, CrashReportClient) or more than 2 GB of VRAM in use. Set MSH_FORCE_GPU = True only after the Unreal lane says go.
#  * All files go to /content/mashtots/ (local) and MyDrive/x3dlab/mashtots/ (Drive). Nothing goes under /content/x3due or /content/shroud_ue.
#  * No runtime restart, no pkill, no drive force_remount anywhere.
#
# THE RUN, in order (smoke first, then core; full is a separate decision, see the budget line). Grades: M = Measured, E = Estimate.
#   cell                           where  time on the G4                                   VRAM
#   MSH-0  card + guard            CPU    ~5 s                                             0
#   MSH-1  configuration (form)    -      instant                                          0
#   MSH-2  source from Drive       CPU    ~5 s (checks the bundle's sha256)                0
#   MSH-3  packages + versions     CPU    ~20 s (private folder, kernel untouched)         0
#   MSH-4  doctor                  GPU    ~1-2 min E                                       ~1 GB E
#   MSH-5  download list           CPU    instant; nothing fetched. Read it, tick MSH_I_APPROVE_DOWNLOADS in MSH-1, rerun MSH-1
#   MSH-6  fetch + build data      CPU    smoke ~1-2 min | core ~6-10 min | full ~15-20 min  E (sandbox M: 16 s fetch + 63 s build, 4 CPUs)
#   MSH-7  token bill (H1)         CPU    ~15-30 s (sandbox M: 11 s; tokenizer files ~90 MB)  0
#   MSH-8  our tokenizers          CPU    smoke ~1-2 min | core/full ~7-20 min  E (sandbox M: 116 s, 4 CPUs)
#   MSH-9  FREEZE                  CPU    instant (sha256 of PREREG.md and the code, before any model trains)
#   MSH-10 cost bench              GPU    smoke ~3 min | core ~10 min | full ~20-30 min  E    printed per size (M); E: compiled ~8-20 GB at 6M-15M,
#                                                                                           ~27-32 GB at 150M; eager (MSH_COMPILE=False) up to ~52 GB
#   MSH-11 train the grid          GPU    smoke ~5-10 min | core ~2.5-5 h | full ~13-25 h  E (MSH-10 prints the projection from measured speed)
#   MSH-12 analyze (H1-H6)         CPU    ~1-3 min
#   MSH-13 X3D export              GPU    ~1 min, <2 GB E
#   MSH-14 package + kernel audit  CPU    ~10 s
# BUDGET at 8.7 units/h (third-party G4 rate; check Colab's own figure): smoke ~3 units, core ~35 (27-46), full ~160 (120-225) E.
#   full re-trains 6M-40M on the bigger tier-2 data (each profile has its own data and runs), so smoke+core+full is ~200 units against the
#   plan's ~150. PLAN.md's order of cuts: MSH_ARMS_OVERRIDE="bpe,mashtots" (drops bytes, ~1/3 of full). Use MSH_MAX_HOURS (e.g. 4) to hand the
#   GPU back to the Unreal lane between sessions; MSH-11 resumes from the Drive checkpoint.
# Time and VRAM sources: the sandbox rehearsal (Measured, 4-core CPU) and a roofline estimate for the RTX PRO 6000 Blackwell SE at 500 TFLOPS
# dense bf16 and 1.6 TB/s (Lenovo Press LP2263), 14-34 % MFU by size. All GPU times are Estimates until MSH-10 measures this card.
# Every cell can be run again; finished runs are skipped and an unfinished one resumes from its Drive checkpoint.

# %%
#@title MSH-0 · Mashtots card + GPU guard (FIRST Mashtots cell; CPU, ~5 s, 0 GB VRAM)
import types as _msh_types
MSH = globals().get("MSH") or _msh_types.SimpleNamespace()
del _msh_types
def _msh():
    import os, sys, json, shutil, subprocess, hashlib, time
    MSH.ROOT = os.environ.get("MSH_ROOT", "/content/mashtots")     # MSH_ROOT is set only by the sandbox rehearsal
    MSH.VERSION = "mashtots-poc v1.2 (shared-kernel edition)"
    os.makedirs(MSH.ROOT, exist_ok=True)
    UNREAL = ("UnrealEditor", "UnrealBuildTool", "ShaderCompileWorker", "CrashReportClient", "blender")   # plus the VRAM and utilisation tests below (they catch Chromium benches too)
    def gpu_state():
        if not shutil.which("nvidia-smi"):
            return dict(gpu=["no GPU (nvidia-smi missing)", "-", "0", "0", "0", "-"], apps=[], unreal_procs=[])
        q = lambda a: subprocess.run(["nvidia-smi", a, "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout.strip()
        apps = [x.split(", ") for x in q("--query-compute-apps=pid,process_name,used_memory").splitlines() if x.strip()]
        g = q("--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,compute_cap").split(", ")
        procs = subprocess.run(["ps", "-eo", "pid,comm,args"], capture_output=True, text=True).stdout.splitlines()
        unreal = [p.strip()[:140] for p in procs if any(u in p for u in UNREAL[:5])]
        return dict(gpu=g, apps=apps, unreal_procs=unreal)
    def gpu_guard(need_gb=2.0):
        if getattr(MSH, "LOCAL", False):
            print("sandbox dry run: GPU guard skipped (CPU only)")
            return
        s = gpu_state()
        name, drv, tot, used, util = s["gpu"][:5]
        print(f"GPU guard: {name}, driver {drv}, {used}/{tot} MiB used, util {util}%, compute apps {len(s['apps'])}, Unreal processes {len(s['unreal_procs'])}")
        for a in s["apps"]:
            print("   app:", " | ".join(a))
        for p in s["unreal_procs"]:
            print("   unreal:", p)
        busy = s["unreal_procs"] or float(used) > 2048 or float(util) > 20
        if busy and not globals().get("MSH_FORCE_GPU", False):
            raise SystemExit("GPU guard: the GPU is in use (Unreal or another job). Nothing was started. Wait for the Unreal lane's go, "
                             "then run this cell again (or set MSH_FORCE_GPU = True in MSH-1 if the Unreal lane says the GPU is free).")
        if float(tot) - float(used) < need_gb * 1024:
            raise SystemExit(f"GPU guard: less than {need_gb} GB VRAM free; nothing was started.")
        print("GPU guard: free, go." if not busy else "GPU guard: busy, but MSH_FORCE_GPU is set: going on.")
    MSH.gpu_state, MSH.gpu_guard = gpu_state, gpu_guard
    # snapshot of the kernel for the audit in MSH-14: which globals exist (by identity), sys.path and os.environ
    if not hasattr(MSH, "SNAP"):
        g = globals()
        MSH.SNAP = dict(t=time.time(), globals={k: id(v) for k, v in g.items() if not k.startswith("_")},
                        path=list(sys.path), env=hashlib.sha256(json.dumps(sorted(os.environ.items())).encode()).hexdigest())
    s = gpu_state()
    MSH.HWCARD = dict(gpu=s["gpu"], cpus=os.cpu_count(), ram_gb=round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1),
                      disk_free_gb=round(shutil.disk_usage(MSH.ROOT).free / 1e9, 1), python=sys.version.split()[0],
                      kernel_torch=_ver("torch"), kernel_numpy=_ver("numpy"))
    print(MSH.VERSION)
    print(json.dumps(MSH.HWCARD, indent=1))
    print("Unreal processes now:", len(s["unreal_procs"]), "| GPU compute apps now:", len(s["apps"]))
def _ver(m):
    try:
        import importlib.metadata as md
        return md.version(m)
    except Exception:
        return "missing"
_msh(); del _msh, _ver

# %%
#@title MSH-1 · Configuration (form; instant). Rerun after changing a field.
MSH_PROFILE = "smoke"  #@param ["smoke", "core", "full"]
MSH_RUN_NAME = "g4a"  #@param {type:"string"}
MSH_I_APPROVE_DOWNLOADS = False  #@param {type:"boolean"}
MSH_UNITS_PER_HOUR = 8.7  #@param {type:"number"}
MSH_MAX_HOURS = 0.0  #@param {type:"number"}
MSH_ARMS_OVERRIDE = ""  #@param {type:"string"}
MSH_SIZES_OVERRIDE = ""  #@param {type:"string"}
MSH_EXTRA_SOURCES = ""  #@param {type:"string"}
MSH_ALLOW_MIRRORS = True  #@param {type:"boolean"}
MSH_COMPILE = True  #@param {type:"boolean"}
MSH_WORKERS = 0  #@param {type:"integer"}
MSH_FORCE_GPU = False  #@param {type:"boolean"}
MSH_DRIVE_BASE = "x3dlab/mashtots"  #@param {type:"string"}
def _msh():
    import os, sys, pathlib
    MSH.IN_COLAB = "google.colab" in sys.modules
    MSH.LOCAL = os.environ.get("MP_LOCAL") == "1"            # the sandbox's dry run only; never set in Colab
    MSH.PROFILE, MSH.RUN_NAME = MSH_PROFILE, MSH_RUN_NAME
    root = pathlib.Path(MSH.ROOT)
    MSH.SRC, MSH.DATA = root / "src", root / ("local" if MSH.LOCAL else MSH.PROFILE)
    MSH.RUNS, MSH.RESULTS, MSH.DEPS = MSH.DATA / "runs", MSH.DATA / "results", root / "pydeps"
    for d in (MSH.SRC, MSH.DATA, MSH.RUNS, MSH.RESULTS):
        d.mkdir(parents=True, exist_ok=True)
    MSH.EXTRA = tuple(x.strip() for x in MSH_EXTRA_SOURCES.split(",") if x.strip())
    MSH.WORKERS = MSH_WORKERS or (max(1, min(40, (os.cpu_count() or 2) - 4)) if not MSH.LOCAL else 2)
    MSH.DRIVE_DIR = f"/content/drive/MyDrive/{MSH_DRIVE_BASE}"
    MSH.DRIVE_OUT = f"{MSH.DRIVE_DIR}/runs/{MSH.RUN_NAME}-{MSH.PROFILE}" if MSH.IN_COLAB else None
    MSH.DRIVE_RUNS = f"{MSH.DRIVE_OUT}/runs" if MSH.DRIVE_OUT else None
    print(f"{MSH.VERSION} | profile {MSH.PROFILE} | run {MSH.RUN_NAME} | downloads approved: {MSH_I_APPROVE_DOWNLOADS} | workers {MSH.WORKERS} "
          f"| local data {MSH.DATA} | Drive {MSH.DRIVE_OUT} | force GPU: {MSH_FORCE_GPU}")
_msh(); del _msh

# %%
#@title MSH-2 · Source code from Drive (CPU, ~5 s). Needs MyDrive/x3dlab/mashtots/mashtots_src_v1.2.tar.gz
MSH_BUNDLE_SHA256 = "8588fcfaae860351e420fd39a7e6619367c034f91adc996241f503c4d281945f"
def _msh():
    import os, sys, tarfile, hashlib, shutil, pathlib, importlib
    if MSH.IN_COLAB and not os.path.ismount("/content/drive"):
        from google.colab import drive
        drive.mount("/content/drive")                       # no force_remount: if the Unreal lane mounted it, this is skipped
    bundle = pathlib.Path(os.environ.get("MSH_BUNDLE", f"{MSH.DRIVE_DIR}/mashtots_src_v1.2.tar.gz"))
    h = hashlib.sha256(bundle.read_bytes()).hexdigest()
    print("bundle", bundle, bundle.stat().st_size, "bytes, sha256", h[:16])
    if MSH_BUNDLE_SHA256.startswith("__"):
        print("(no pinned hash in this cell; the bundle's MANIFEST is still checked file by file)")
    elif h != MSH_BUNDLE_SHA256:
        raise SystemExit(f"bundle hash differs from the one in this cell ({MSH_BUNDLE_SHA256[:16]}): stop and tell Claude")
    tmp = pathlib.Path(MSH.ROOT) / "bundle_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    with tarfile.open(bundle) as t:
        t.extractall(tmp, filter="data")
    man = dict(line.split("  ")[::-1] for line in (tmp / "MANIFEST.sha256").read_text().splitlines() if line.strip())
    bad = [n for n, v in man.items() if hashlib.sha256((tmp / n).read_bytes()).hexdigest() != v]
    if bad:
        raise SystemExit(f"bundle files do not match the MANIFEST: {bad}")
    for n in man:
        dst = (MSH.DATA / n) if n.startswith("udhr/") else (MSH.SRC / n)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(tmp / n, dst)
    shutil.rmtree(tmp, ignore_errors=True)
    if str(MSH.SRC) not in sys.path:
        sys.path.append(str(MSH.SRC))                       # appended: never shadows the Unreal lane's modules
    for m in [m for m in sys.modules if m == "nb_helpers" or m.startswith("mp_")]:
        del sys.modules[m]                                  # a rerun picks up a new bundle
    H = importlib.import_module("nb_helpers")
    assert pathlib.Path(H.__file__).parent == MSH.SRC, H.__file__
    H.PY, H.DEPS = sys.executable, str(MSH.DEPS)
    env = dict(os.environ)                                  # a private copy: the kernel's os.environ is not written
    env["PYTHONPATH"] = os.pathsep.join([str(MSH.DEPS)] + [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p])
    env["HF_HOME"] = f"{MSH.ROOT}/hf"
    env["TIKTOKEN_CACHE_DIR"] = f"{MSH.ROOT}/tiktoken"
    env["MP_UDHR_DIR"] = str(MSH.DATA / "udhr")
    env["PYTHONUNBUFFERED"] = "1"
    if MSH.IN_COLAB:
        try:
            from google.colab import userdata               # a Hugging Face token in Colab's Secrets (key icon), if you added one
            tok = userdata.get("HF_TOKEN")
            if tok:
                env["HF_TOKEN"] = tok
        except Exception:
            pass
    print("HF token for gated tokenizers:", "yes (not printed)" if env.get("HF_TOKEN") else "no (mirrors used only when byte-identical)")
    H.ENV, H.SHARED, MSH.H = env, True, H
    print("wrote", len(man), "files:")
    for n in sorted(man):
        print(f"  {man[n][:12]}  {n}")
_msh(); del _msh

# %%
#@title MSH-3 · Packages (private folder) and versions (CPU, ~20 s). The kernel's packages are not changed.
def _msh():
    MSH.H.install()
    MSH.H.env_report()
_msh(); del _msh

# %%
#@title MSH-4 · Doctor: GPU, model code, tokenizers, network, disk, Drive (GPU ~1-2 min, ~1 GB VRAM). Go on only on ALL GOOD.
def _msh():
    import sys, subprocess
    MSH.gpu_guard(need_gb=4)
    # mp_data is imported in a subprocess, not in the kernel: at import it puts its own folder FIRST on sys.path
    code = (f"import sys; sys.path.insert(0, {str(MSH.SRC)!r}); import mp_data as D; "
            f"print(D.plan({(MSH.PROFILE if not MSH.LOCAL else 'local')!r}, {MSH.EXTRA!r})[1])")
    total = float(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=MSH.H.ENV, check=True).stdout.strip())
    # disk: the pipeline writes about 7x the download (raw + pools + encoded tokens + a 2.2 GB checkpoint at 150M); full needs about 45 GB
    MSH.OK = MSH.H.doctor(MSH.SRC, MSH.DATA, MSH.DRIVE_OUT, need_gb=max(2.0, 7 * total / 1e9), compile_=MSH_COMPILE)
_msh(); del _msh

# %%
#@title MSH-5 · What would be downloaded for this profile (instant; nothing is fetched here)
def _msh():
    import sys
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_data.py"), "plan", "--profile", MSH.PROFILE if not MSH.LOCAL else "local", "--extra", ",".join(MSH.EXTRA)])
    print("\nNVIDIA: no Armenian text data in the Nemotron datasets (checked 2026-10-28); Nemotron is measured through its tokenizer only.")
    print("To go on: tick MSH_I_APPROVE_DOWNLOADS in MSH-1, run MSH-1 again, then MSH-6." if not MSH_I_APPROVE_DOWNLOADS else "Downloads approved in MSH-1.")
_msh(); del _msh

# %%
#@title MSH-6 · Fetch (resume-safe) and build the data: eval sets first, then cleaned, decontaminated, deduplicated pools (CPU + network)
def _msh():
    import sys, time
    t0 = time.time()
    if MSH.LOCAL:
        print("sandbox dry run: no downloads")
    else:
        assert MSH_I_APPROVE_DOWNLOADS, "tick MSH_I_APPROVE_DOWNLOADS in MSH-1 after reading the list in MSH-5"
        MSH.H.sh([sys.executable, str(MSH.SRC / "mp_data.py"), "fetch", "--profile", MSH.PROFILE, "--root", str(MSH.DATA), "--extra", ",".join(MSH.EXTRA)])
    if not (MSH.DATA / "data_stats.json").exists():
        MSH.H.sh([sys.executable, str(MSH.SRC / "mp_data.py"), "build", "--profile", MSH.PROFILE if not MSH.LOCAL else "local", "--root", str(MSH.DATA),
                  "--workers", str(MSH.WORKERS), "--extra", ",".join(MSH.EXTRA)])
    else:
        print("data already built:", MSH.DATA / "data_stats.json")
    import json
    ds = json.loads((MSH.DATA / "data_stats.json").read_text())
    print("classifier (single UD test sentences):", ds["classifier"]["accuracy"])
    print("pools MB:", {k: round(v["bytes"] / 1e6, 1) for k, v in ds["pools"].items()})
    print("dialect x spelling (MB):", {k: round(v / 1e6, 1) for k, v in ds.get("crosstab_bytes", {}).items()})
    # annotation/: the first batch for participation/annotate.html (its KEY file stays with the coordinator, as in the original notebook)
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["data_stats.json", "fetch_log.json", "annotation"])
    print(f"MSH-6 wall time {time.time() - t0:.0f} s (CPU: {MSH.HWCARD['cpus']} cores, {MSH.WORKERS} workers)")
_msh(); del _msh

# %%
#@title MSH-7 · The token bill (H1): eight big-lab tokenizers on the UDHR and on four treebanks (CPU, ~2-4 min)
def _msh():
    import sys
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_tok.py"), "bill", "--root", str(MSH.DATA), "--out", str(MSH.RESULTS)]
             + (["--allow-mirrors"] if MSH_ALLOW_MIRRORS else []))
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["results"])
_msh(); del _msh

# %%
#@title MSH-8 · Our tokenizers: suffix inventory, bpe / mashtots / two ablations, fertility, then encode the pools (CPU)
def _msh():
    import sys, time
    t0 = time.time()
    if not (MSH.DATA / "tokenizers" / "train_report.json").exists():
        MSH.H.sh([sys.executable, str(MSH.SRC / "mp_tok.py"), "train", "--root", str(MSH.DATA), "--sample-mb", "300"])
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_tok.py"), "fertility", "--root", str(MSH.DATA), "--out", str(MSH.RESULTS)])
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_tok.py"), "encode", "--root", str(MSH.DATA), "--workers", str(MSH.WORKERS)])
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["tokenizers", "results", "tokens/encode_report.json"])
    print(f"MSH-8 wall time {time.time() - t0:.0f} s")
_msh(); del _msh

# %%
#@title MSH-9 · FREEZE the pre-registration and the code before any model trains (instant)
def _msh():
    MSH.FROZEN = MSH.H.freeze(MSH.SRC, MSH.DATA, MSH.PROFILE, dict(build="v1.2-shared", run=MSH.RUN_NAME, hardware=MSH.HWCARD["gpu"]))
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["PREREG.md", "PREREG.sha256"])
_msh(); del _msh

# %%
#@title MSH-10 · What will training cost? Measured throughput and peak VRAM per (tokenizer, size), then the projection (GPU, ~2-6 min)
def _msh():
    import json
    MSH.gpu_guard(need_gb=30 if MSH_COMPILE else 45)      # eager mode keeps the full fp32 logits: ~36 GB peak even at 6M
    MSH.SPECS = MSH.H.grid(MSH.PROFILE, MSH_ARMS_OVERRIDE, MSH_SIZES_OVERRIDE)
    MSH.BENCH = MSH.H.bench(MSH.SRC, MSH.DATA, MSH.SPECS, compile_=MSH_COMPILE)
    print(f"\n{'arm':<10}{'size':>6}{'tok/s':>12}{'peak VRAM GB':>14}   (Measured on {MSH.HWCARD['gpu'][0]})")
    for (arm, size), b in sorted(MSH.BENCH.items(), key=lambda kv: (MSH.H.C.non_embedding_params(kv[0][1]), kv[0][0])):
        pk = b.get("peak_mem_gb")
        print(f"{arm:<10}{size:>6}{b['tok_per_s']:>12,.0f}{(pk if pk is not None else float('nan')):>14.1f}")
    MSH.PLAN_ROWS, MSH.PLAN_HOURS = MSH.H.project(MSH.SPECS, MSH.BENCH, MSH_UNITS_PER_HOUR)
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["bench"])
_msh(); del _msh

# %%
#@title MSH-11 · Train the grid, smallest first (GPU; resume-safe, checkpoints to Drive every 15 min, finished runs skipped)
def _msh():
    import json, time
    MSH.gpu_guard(need_gb=30 if MSH_COMPILE else 45)
    assert (MSH.DATA / "PREREG.sha256").exists(), "run MSH-9 (Freeze) first"
    t0, before = time.time(), sorted(p.parent.name for p in MSH.RUNS.glob("*/done.json"))
    try:
        MSH.DONE, MSH.LEFT = MSH.H.train_grid(MSH.SRC, MSH.DATA, MSH.SPECS, MSH.RUNS, MSH.DRIVE_RUNS, max_hours=MSH_MAX_HOURS, compile_=MSH_COMPILE)
        status = "ok"
    except BaseException as exc:                          # an interrupt or a failed run still gets its wall time logged
        status = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        # a resumed run's own train_seconds counts only its last session; this log keeps every session's wall time (for O3/O4 and the bill)
        rec = dict(start=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t0)), seconds=round(time.time() - t0, 1), status=status,
                   finished_before=before, finished_after=sorted(p.parent.name for p in MSH.RUNS.glob("*/done.json")),
                   compile=MSH_COMPILE, max_hours=MSH_MAX_HOURS, gpu=MSH.HWCARD["gpu"][0])
        with open(MSH.DATA / "train_wall.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        print(f"MSH-11 session: {rec['seconds'] / 3600:.2f} h, {status}; logged to train_wall.jsonl")
        MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["train_wall.jsonl"])
_msh(); del _msh

# %%
#@title MSH-12 · Analyze exactly as pre-registered: verdicts H1-H6, tables, figures (CPU, ~1-3 min)
def _msh():
    import sys
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_analyze.py"), "--root", str(MSH.DATA), "--runs", str(MSH.RUNS), "--out", str(MSH.RESULTS)])
    MSH.H.show(sorted((MSH.RESULTS / "figs").glob("*.png")))
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["results"])
_msh(); del _msh

# %%
#@title MSH-13 · Export the real model for the X3D scene: 36 x 36 letter attention, letter embeddings, the landing's two texts (GPU, ~1-3 min)
def _msh():
    import sys
    if not MSH.LOCAL:
        MSH.gpu_guard(need_gb=8)
    MSH.H.sh([sys.executable, str(MSH.SRC / "mp_export.py"), "--root", str(MSH.DATA), "--runs", str(MSH.RUNS),
              "--out", str(MSH.RESULTS / "mashtots_model_export.json"), "--device", "cpu" if MSH.LOCAL else "cuda"])
    MSH.H.show([MSH.RESULTS / "figs" / "export_preview.png"])
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["results"])
_msh(); del _msh

# %%
#@title MSH-14 · Package to Drive, then audit the shared kernel (CPU, ~10 s)
def _msh():
    import os, sys, json, time, hashlib, platform, subprocess
    pk = subprocess.run([sys.executable, "-c", "import importlib.metadata as m\nfor p in ('torch','tokenizers','tiktoken','pyarrow','huggingface_hub','numpy'):\n"
                         "    print(p, m.version(p))"], capture_output=True, text=True, env=MSH.H.ENV).stdout.split("\n")
    info = dict(version=MSH.VERSION, profile=MSH.PROFILE, run=MSH.RUN_NAME, finished=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                hardware=MSH.HWCARD, python=platform.python_version(), subprocess_packages=[x for x in pk if x],
                runs_done=sorted(p.parent.name for p in MSH.RUNS.glob("*/done.json")),
                projected_hours=round(getattr(MSH, "PLAN_HOURS", 0.0), 2), units_per_hour=MSH_UNITS_PER_HOUR,
                train_wall_hours=round(sum(json.loads(x)["seconds"] for x in open(MSH.DATA / "train_wall.jsonl")) / 3600, 3)
                if (MSH.DATA / "train_wall.jsonl").exists() else 0.0)
    (MSH.DATA / "run_info.json").write_text(json.dumps(info, indent=1))
    MSH.H.checkpoint(MSH.DATA, MSH.DRIVE_OUT, ["run_info.json", "results", "data_stats.json", "PREREG.sha256", "tokenizers", "bench", "train_wall.jsonl"])
    print(json.dumps(info, indent=1))
    # the kernel audit: every global that existed before MSH-0 still points at the same object; sys.path only gained MSH.SRC; os.environ unchanged
    g, snap = globals(), MSH.SNAP
    changed = [k for k, i in snap["globals"].items() if k in g and id(g[k]) != i and k != "MSH" and not k.startswith("MSH_")]
    gone = [k for k in snap["globals"] if k not in g]
    new = sorted(k for k in g if not k.startswith("_") and k not in snap["globals"] and k != "MSH" and not k.startswith("MSH_"))
    path_added = [p for p in sys.path if p not in snap["path"]]
    path_prefix_ok = sys.path[:len(snap["path"])] == snap["path"]
    env_same = hashlib.sha256(json.dumps(sorted(os.environ.items())).encode()).hexdigest() == snap["env"]
    print("\nKERNEL AUDIT (since MSH-0):")
    print("  globals rebound (by any cell since MSH-0, the Unreal lane's own included):", changed or "none", "| removed:", gone or "none")
    print("  new globals (other lanes' cells run in between count here too):", new or "none")
    print("  sys.path added (at the end only):", path_added or "none", "| earlier entries in their old order:", path_prefix_ok,
          "| os.environ unchanged:", env_same)
    print("DONE. Results:", MSH.DRIVE_OUT or MSH.DATA)
_msh(); del _msh
