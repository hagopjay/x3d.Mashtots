#!/usr/bin/env python3
"""Rehearse mashtots_g4_cells.py inside a fake SHARED kernel, then prove the Unreal lane's state survived.

usage: MP_UD_DIR=<folder with the four UD treebank repos> python3 sim_shared_kernel.py BUNDLE.tar.gz WORKDIR [cells.py]

The cells run top to bottom in one namespace (as Colab runs them), in the sandbox's dry-run mode (MP_LOCAL=1: no downloads, tiny model, CPU).
Before MSH-0 the namespace is seeded with the Unreal lane's reserved globals and module names (its 05:11Z list) and a few Unreal cells run
BETWEEN the Mashtots cells, the way the shared notebook interleaves them. At the end it checks:
  1. every Unreal global still points at the same object, and every reserved module is still the same module object;
  2. the Mashtots cells created no globals except MSH and MSH_*;
  3. os.environ is byte-identical; sys.path only gained MSH.SRC, at the END;
  4. nothing was written under /content/x3due or /content/shroud_ue, and every Mashtots file is under WORKDIR;
  5. the kernel's own site-packages were not touched (pip --target only).
Exit code 0 = all five hold.
"""
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import traceback
import types

bundle, work = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
cells_py = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "mashtots_g4_cells.py")
work.mkdir(parents=True, exist_ok=True)
os.environ.update(MP_LOCAL="1", MSH_ROOT=str(work), MSH_BUNDLE=os.path.abspath(bundle))
os.environ.setdefault("MP_CENSUS_DIR", "")

RESERVED = ("LAB PLAN HW BL WORK DRIVE_DIR SCN IMP RND CARD SH_LOOK SH_CAM SHD R2 R2_KEEP R4 R5 CAM1 CAM2 EV_P1 EV_P2 FXC FX SUBTLE LOOKS STORY "
            "RUNG4K PT4K S2 S3 S4 S5 S6 ok tier compare CMP SCENES EXTRA SCENE_DIR OWN ENGINE_VERSION FLIP FLIP_PAIRS labels key v eng").split()
MODULES = "pipeline lines engines showcase ucopy uerun project x3dscene staging".split()
ns = {"__name__": "__main__", "__builtins__": __builtins__}
for k in RESERVED:
    ns[k] = types.SimpleNamespace(owner="unreal", name=k)
for m in MODULES:
    sys.modules[m] = types.ModuleType(m)
    ns[m] = sys.modules[m]
ids = {k: id(ns[k]) for k in RESERVED + MODULES}
mods = {m: id(sys.modules[m]) for m in MODULES}
env0 = hashlib.sha256(json.dumps(sorted(os.environ.items())).encode()).hexdigest()
path0 = list(sys.path)
site0 = {p: sorted(os.listdir(p)) for p in sys.path if p.endswith("-packages") and os.path.isdir(p)}

UNREAL_CELLS = [  # what an Unreal cell between ours might do: read its globals, rebind its own names, import its modules
    "R5 = types_r5 = __import__('types').SimpleNamespace(owner='unreal', name='R5')\nok = ok\nimport pipeline, lines\nCARD.touched = True",
    "assert LAB.owner == 'unreal' and HW.owner == 'unreal'\nimport staging\nSCENES = SCENES",
]
src = open(cells_py).read()
cells = [c for c in re.split(r"^# %%\s*$", src, flags=re.M)[1:] if c.strip()]
print(f"{len(cells)} cells in {cells_py}")
t_all = time.time()
for i, c in enumerate(cells):
    title = next((ln for ln in c.splitlines() if ln.startswith("#@title")), "?")
    print(f"\n=== {title[8:100]}", flush=True)
    t0 = time.time()
    try:
        exec(compile(c, f"<{title[8:20].strip()}>", "exec"), ns)
    except SystemExit as e:
        print(f"!!! SystemExit in {title}: {e}")
        sys.exit(1)
    except Exception:
        traceback.print_exc()
        print(f"!!! failed after {time.time() - t0:.1f}s")
        sys.exit(1)
    print(f"--- ok ({time.time() - t0:.1f}s)", flush=True)
    if i in (2, 8):     # interleave an Unreal cell after MSH-2 and after MSH-8
        uc = UNREAL_CELLS[0 if i == 2 else 1]
        exec(uc, ns)
        if "R5" in uc:  # the Unreal cell rebinds R5 itself: that is its right, so follow it
            ids["R5"] = id(ns["R5"])
        print("    (an Unreal cell ran here)")

print(f"\ncells finished in {time.time() - t_all:.0f} s\n\nAUDIT")
fails = []
changed = [k for k in RESERVED + MODULES if id(ns.get(k)) != ids[k]]
fails += [f"Unreal global rebound or removed: {changed}"] if changed else []
mchanged = [m for m in MODULES if id(sys.modules.get(m)) != mods[m]]
fails += [f"Unreal module replaced in sys.modules: {mchanged}"] if mchanged else []
UNREAL_NEW = {"types_r5"}
new = sorted(k for k in ns if k not in ids and not (k.startswith("__") and k.endswith("__")) and k != "MSH" and not k.startswith("MSH_") and k not in UNREAL_NEW)
fails += [f"new non-MSH globals: {new}"] if new else []
env1 = hashlib.sha256(json.dumps(sorted(os.environ.items())).encode()).hexdigest()
fails += ["os.environ changed"] if env1 != env0 else []
added = [p for p in sys.path if p not in path0]
if added != [str(ns["MSH"].SRC)] or sys.path[: len(path0)] != path0:
    fails.append(f"sys.path changed beyond appending MSH.SRC: added {added}, prefix intact {sys.path[:len(path0)] == path0}")
for p in ("/content/x3due", "/content/shroud_ue"):
    if os.path.exists(p):
        fails.append(f"{p} exists")
site1 = {p: sorted(os.listdir(p)) for p in site0}
fails += ["site-packages changed"] if site1 != site0 else []
outside = [str(p) for p in (ns["MSH"].SRC, ns["MSH"].DATA, ns["MSH"].DEPS) if not str(p).startswith(str(work))]
fails += [f"Mashtots paths outside WORKDIR: {outside}"] if outside else []
print("  Unreal globals intact:", not changed, f"({len(RESERVED) + len(MODULES)} names)")
print("  Unreal modules intact:", not mchanged)
print("  new non-MSH globals:", new or "none")
print("  os.environ identical:", env1 == env0)
print("  sys.path: appended", added)
print("  site-packages untouched:", site1 == site0)
print("  MSH attributes:", sorted(vars(ns["MSH"])))
print("\nPASS" if not fails else "\nFAIL:\n  " + "\n  ".join(fails))
sys.exit(1 if fails else 0)
