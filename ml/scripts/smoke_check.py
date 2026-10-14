"""Offline ML smoke check — fast, deterministic, no downloads, no model load.

Run from ml/ with the isolated env:
    .\\.venv\\Scripts\\python.exe scripts\\smoke_check.py

Verifies (exit 0 = pass, non-zero = fail with a message):
1. CROHME vocab invariants (size, special tokens, documented alphabet gaps).
2. Evaluator canonicalizer + Levenshtein unit vectors (guards evaluate_baseline.py).
3. Committed experiment JSONs keep the expected schema (proves the recorded
   baseline artifacts are intact and comparable).
4. Render/label fixtures referenced by the experiments exist on disk.

Slow model inference is NOT run here — it is covered by the gated backend E2E
(EIGEN_TEST_WORKER=1) and the scripts/run_posformer.py experiments.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pl_compat  # noqa: E402

pl_compat.install()
sys.path.insert(0, os.environ.get(
    "POSFORMER_CODE",
    r"C:\Users\Swarnim\AppData\Local\Temp\opencode\PosFormer-code"))
from Pos_Former.datamodule import vocab  # noqa: E402

import evaluate_baseline as ev  # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


# 1. vocab invariants (110 dictionary words + <pad>/<sos>/<eos> = 113 total)
check("vocab-size-113", len(vocab) == 113, f"len={len(vocab)}")
check("vocab-specials",
      vocab.word2idx.get("<pad>") == 0 and vocab.word2idx.get("<sos>") == 1
      and vocab.word2idx.get("<eos>") == 2)
check("vocab-missing-caps-documented",
      all(c not in vocab.word2idx for c in "ZDJKOQUW"),
      "dictionary must lack Z D J K O Q U W (see baseline report)")
check("vocab-core-symbols",
      all(t in vocab.word2idx for t in ["\\frac", "\\sqrt", "\\sum", "x", "=", "("]))

# 2. canonicalizer + lev vectors
check("canon-strips", ev.canon("\\frac { 1 } { 2 }") == "frac12")
check("canon-case", ev.canon("X") == "X" and ev.canon("X") != ev.canon("x"))
check("lev-basic", ev.lev("kitten", "sitting") == 3)
check("lev-empty", ev.lev("", "abc") == 3 and ev.lev("", "") == 0)
check("tokenize-sqrt", ev.tokenize_gt("sqrt(4)") == ["\\sqrt", "(", "4", ")"])
check("tokenize-frac", ev.tokenize_gt("\\frac{1}{2}") == ["\\frac", "{", "1", "}", "{", "2", "}"])

# 3. experiment artifact schema
exp = os.path.join(HERE, "..", "experiments")
for fname in ["posformer_run1.json", "posformer_run2_temp05.json"]:
    p = os.path.join(exp, fname)
    if not os.path.exists(p):
        check(f"artifact-{fname}", False, "missing file")
        continue
    run = json.load(open(p, encoding="utf-8"))
    ok = (isinstance(run.get("results"), list) and len(run["results"]) > 0
          and all(set(r) >= {"id", "gt", "pred", "latency_s"} for r in run["results"])
          and isinstance(run.get("beam", {}).get("temperature"), (int, float)))
    check(f"artifact-{fname}", ok, "schema drift")

# 4. fixtures on disk (first 3 ids of run1 must have _b.png renders + labels row)
renders = os.path.join(HERE, "..", "data", "renders", "test")
labels_p = os.path.join(renders, "labels.tsv")
rows = {}
if os.path.exists(labels_p):
    for line in open(labels_p, encoding="utf-8"):
        line = line.rstrip("\n")
        if line:
            sid, gt = line.split("\t", 1)
            rows[sid] = gt
run1 = json.load(open(os.path.join(exp, "posformer_run1.json"), encoding="utf-8"))
sample = run1["results"][:3]
check("fixtures-renders",
      all(os.path.exists(os.path.join(renders, f"{r['id']}_b.png")) for r in sample))
check("fixtures-labels-match",
      all(rows.get(r["id"]) == r["gt"] for r in sample))

print(f"{'SMOKE OK' if not FAILURES else f'{len(FAILURES)} FAILURES: {FAILURES}'}")
sys.exit(1 if FAILURES else 0)
