#!/usr/bin/env python3
"""Build mashtots_src_v1.1.tar.gz for the shared-kernel cells (MSH-2 reads it from MyDrive/x3dlab/mashtots/).

usage: python3 -I make_bundle.py [OUT_DIR]      (default: this folder)
Contents: the PoC code (the same files the standalone notebook embeds), PREREG.md, PREDICTIONS.md, the two UDHR texts, and MANIFEST.sha256.
The tarball is deterministic (sorted names, mtime 0, uid/gid 0), so the same sources always give the same sha256.
"""
import gzip
import hashlib
import io
import os
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.dirname(HERE)
CODE = ["mp_common.py", "mp_data.py", "mp_tok.py", "mp_model.py", "mp_train.py", "mp_eval.py", "mp_analyze.py", "mp_export.py", "nb_helpers.py",
        "PREREG.md", "PREDICTIONS.md"]
FILES = [(n, os.path.join(POC, n)) for n in CODE] + [(f"udhr/{n}", os.path.join(HERE, "udhr", n)) for n in ("udhr_hye.xml", "udhr_eng.xml")]
out_dir = sys.argv[1] if len(sys.argv) > 1 else HERE
out = os.path.join(out_dir, "mashtots_src_v1.1.tar.gz")
blobs = {n: open(p, "rb").read() for n, p in FILES}
manifest = "".join(f"{hashlib.sha256(b).hexdigest()}  {n}\n" for n, b in sorted(blobs.items())).encode()
blobs["MANIFEST.sha256"] = manifest
raw = io.BytesIO()
with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as t:
    for n in sorted(blobs):
        ti = tarfile.TarInfo(n)
        ti.size, ti.mtime, ti.mode, ti.uid, ti.gid, ti.uname, ti.gname = len(blobs[n]), 0, 0o644, 0, 0, "", ""
        t.addfile(ti, io.BytesIO(blobs[n]))
gz = io.BytesIO()
with gzip.GzipFile(fileobj=gz, mode="wb", mtime=0, filename="") as g:
    g.write(raw.getvalue())
open(out, "wb").write(gz.getvalue())
print(out, len(gz.getvalue()), "bytes, sha256", hashlib.sha256(gz.getvalue()).hexdigest())
print(manifest.decode(), end="")
