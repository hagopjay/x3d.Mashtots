import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import armenian_norm as A

CASES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "armenian_vectors.json")))["cases"]


def test_vectors():
    bad = []
    for c in CASES:
        r = A.find(c["quote"], c["source"])
        if (r["verdict"], r["tier"]) != (c["expect"]["verdict"], c["expect"]["tier"]):
            bad.append((c["name"], r["verdict"], r["tier"]))
    assert len(CASES) >= 20 and not bad, bad
