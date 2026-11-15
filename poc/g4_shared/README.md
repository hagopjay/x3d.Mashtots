# Mashtots PoC on the shared Colab G4 (build v1.1, 15 Nov 2026)

The pre-registered Mashtots study (`../PREREG.md`, H1 to H6) as paste-in cells for the **one Colab G4 kernel that the Unreal lane also uses**.
The science is unchanged from build v1. Only the plumbing changed, so that Mashtots never disturbs Unreal's globals, packages, files or GPU.

| file | what |
|---|---|
| `mashtots_g4_cells.py` | the cells MSH-0 to MSH-14. Paste each `# %%` block as a cell at the end of the shared notebook. The header has time, VRAM and units for each cell |
| `mashtots_src_v1.1.tar.gz` | the code bundle that MSH-2 reads from `MyDrive/x3dlab/mashtots/` (deterministic; sha256 is pinned in MSH-2; MANIFEST inside) |
| `make_bundle.py` | rebuilds the bundle from `../mp_*.py`, `../nb_helpers.py`, `PREREG.md`, `PREDICTIONS.md` and `udhr/` |
| `sim_shared_kernel.py` | rehearsal: runs every cell in a fake shared kernel seeded with the Unreal lane's 57 reserved names and 9 modules, with Unreal cells interleaved. Then it audits globals, sys.modules, sys.path, os.environ and site-packages |
| `udhr/` | the two UDHR texts (eric-muller/udhr, `data/udhr/`), used for the token bill |

## How the cells stay out of the Unreal lane's way

* **One global.** The cells create only `MSH` (a namespace) and the `MSH_*` form fields. Each cell's body runs in a function `_msh`, which the cell deletes when it finishes.
* **No package changes in the kernel.** Missing or too-old requirements go into `/content/mashtots/pydeps` (pip `--target --no-deps`).
  Only subprocesses see that folder, through a private copy of the environment (`nb_helpers.ENV`). numpy, Pillow and torch are never installed.
* **Torch never loads in the kernel.** All GPU work runs in foreground subprocesses, so it queues behind the Unreal cells. `mp_data` is also imported in a subprocess,
  because at import time it would put its folder first on the kernel's `sys.path`. Rehearsal 1 caught this, and it is fixed.
* **GPU guard.** MSH-4, MSH-10, MSH-11 and MSH-13 stop when they find any of these: an Unreal or Blender process, more than 2 GB of VRAM in use, or GPU utilisation above 20 %.
* **Paths.** Files go only to `/content/mashtots/` and `MyDrive/x3dlab/mashtots/`. No restart, no pkill, no force_remount. Advice printed on failure never says "change the runtime type".

## What changed from build v1 (all before any freeze; no G4 run had happened)

| change | why |
|---|---|
| `nb_helpers.PY / ENV / DEPS / SHARED`, private install | shared kernel: no writes to the kernel's packages or `os.environ` |
| `nb_helpers` appends its folder to `sys.path` (it no longer prepends it) | never shadow another lane's modules |
| `checkpoint()` creates the parent folder on Drive | v1 bug: `tokens/encode_report.json` would have failed with FileNotFoundError on Drive |
| `doctor(compile_=...)`; bench cache split into `compiled/` and `eager/` | `MSH_COMPILE=False` is a real fallback, and its projection uses eager speed |
| MSH-11 logs each session's wall time to `train_wall.jsonl` | a resumed run's `train_seconds` counts only its last session |
| doctor disk check is 7x the download, not 5x | full writes about 43 GB from 6.4 GB of downloads |

Rerun `python3 -I make_bundle.py`, then `MP_UD_DIR=<UD repos> python3 sim_shared_kernel.py mashtots_src_v1.1.tar.gz /tmp/sim` (PASS = exit 0).
