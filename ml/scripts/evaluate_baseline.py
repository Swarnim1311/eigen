"""Evaluate Phase-1 PosFormer predictions vs MathWriting ground truth.

Reads experiments/posformer_run1.json, writes ml/reports/inference_baseline.md
(and prints the summary). All strings pass through ONE documented canonicalizer.

Canonicalization (applied identically to GT and prediction):
  canon(s) = s with all whitespace removed, then '\\' removed, then '{'/'}'
  removed. Rationale: CROHME-vocab predictions ('\\sqrt', braces, spaced tokens)
  and MathWriting labels ('sqrt(...)', different spacing) must meet on a common
  string for character error rate. Case is PRESERVED (X vs x counts as error).

Token-level exact match uses tokenize_gt() mapping MathWriting LaTeX to
CROHME-style tokens (documented approximation — organizer caption conventions
are not available offline; see report caveats). Predictions are already
CROHME token sequences (whitespace-split model output).

Metrics: strict token exact-match rate, canonical CER (Levenshtein/len(ref)),
per-sample latency stats, out-of-vocabulary analysis (GT tokens not in the
113-word CROHME vocab can never be predicted exactly).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pl_compat  # noqa: E402

pl_compat.install()
sys.path.insert(0, os.environ.get(
    "POSFORMER_CODE",
    r"C:\Users\Swarnim\AppData\Local\Temp\opencode\PosFormer-code"))
from Pos_Former.datamodule import vocab  # noqa: E402

VOCAB = set(vocab.word2idx.keys())

FUNC_WORDS = {"sqrt": r"\sqrt", "frac": r"\frac"}


def tokenize_gt(label):
    """MathWriting LaTeX -> CROHME-style token list (documented approximation)."""
    toks = []
    i, n = 0, len(label)
    while i < n:
        c = label[i]
        if c.isspace():
            i += 1
            continue
        if c == "\\":
            m = re.match(r"\\[a-zA-Z]+", label[i:])
            if m:
                toks.append(m.group(0))
                i += len(m.group(0))
            else:  # e.g. '\\' line-break in labels -> keep as OOV-flagged token
                toks.append("\\\\")
                i += 2 if label[i + 1:i + 2] == "\\" else 1
            continue
        if c.isalpha():
            m = re.match(r"[a-zA-Z]+", label[i:])
            word = m.group(0)
            toks.append(FUNC_WORDS.get(word, word) if len(word) > 1 else word)
            # NOTE: multi-letter words other than sqrt/frac (e.g. 'sin' as s,i,n
            # vs '\\sin') are ambiguous cross-dataset; single chars pass through,
            # longer unknown words are kept whole and flagged OOV. Handled below:
            if len(word) > 1 and word not in FUNC_WORDS:
                toks[-1] = word  # keep whole; OOV check will flag it
            i += len(word)
            continue
        toks.append(c)
        i += 1
    # split multi-letter non-command words into chars where all chars in vocab
    # (CROHME writes 'sin' as '\\sin', but bare 'xyz' as x y z)
    out = []
    for t in toks:
        if (len(t) > 1 and not t.startswith("\\") and t not in VOCAB
                and all(ch in VOCAB for ch in t)):
            out.extend(list(t))
        else:
            out.append(t)
    return out


def canon(s):
    return re.sub(r"\s+", "", s).replace("\\", "").replace("{", "").replace("}", "")


def lev(a, b):
    m, n = len(a), len(b)
    if m * n == 0:
        return m + n
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ai = a[i - 1]
        for j in range(1, n + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1,
                         prev[j - 1] + (ai != b[j - 1]))
        prev = cur
    return prev[n]


def main():
    run_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "..", "experiments", "posformer_run1.json")
    with open(run_path, encoding="utf-8") as f:
        run = json.load(f)
    results = run["results"]
    rows, cers, lats, oov_n = [], [], [], 0
    exact = 0
    for r in results:
        gt_toks = tokenize_gt(r["gt"])
        pred_toks = r["pred"].split()
        oov = sorted({t for t in gt_toks if t not in VOCAB})
        oov_n += bool(oov)
        match = gt_toks == pred_toks
        exact += match
        c = canon(r["gt"])
        p = canon(r["pred"])
        cer = lev(p, c) / max(len(c), 1)
        cers.append(cer)
        lats.append(r["latency_s"])
        rows.append((r["id"], r["gt"], r["pred"], match, round(cer, 3),
                     r["latency_s"], ",".join(oov) if oov else "-"))
    n = len(rows)
    report = []
    report.append("# Inference baseline — PosFormer best.ckpt x MathWriting excerpt")
    report.append("")
    report.append(f"Samples: {n} (MathWriting excerpt test/, ≤50-rule compliant). "
                  "Renders: white-on-black PNG from InkML (polarity calibrated). "
                  "Device: CPU. Beam: 10/max_len 200/alpha 1.0/T 1.0 (repo config).")
    report.append("")
    report.append("## Aggregate (cross-dataset: CROHME-trained model on MathWriting renders)")
    report.append("")
    report.append(f"- Strict token exact-match rate: {exact}/{n} = {exact/n:.3f}")
    report.append(f"- Mean canonical CER: {sum(cers)/n:.3f} "
                  f"(median {sorted(cers)[n//2]:.3f})")
    report.append(f"- Samples whose GT contains out-of-vocab tokens: {oov_n}/{n} "
                  "(exact match impossible for these by construction)")
    report.append(f"- Latency: mean {sum(lats)/n:.1f}s, min {min(lats):.1f}s, "
                  f"max {max(lats):.1f}s per image (CPU, incl. beam search)")
    report.append("")
    report.append("## Per-sample")
    report.append("")
    report.append("| id | GT (normalizedLabel) | prediction | exact | CER | s | OOV |")
    report.append("|---|---|---|---|---|---|---|")
    for sid, gt, pred, m, cer, lat, oov in rows:
        mark = "YES" if m else "no"
        report.append(f"| {sid} | `{gt}` | `{pred}` | {mark} | {cer} | {lat} | {oov} |")
    report.append("")
    report.append("## Caveats")
    report.append("")
    report.append("- Cross-dataset: checkpoint trained on CROHME renders; test images "
                  "are MathWriting inks rendered 1:1 with PIL (stroke 4px), not "
                  "organizer BMPs. Expect a domain gap vs CROHME-test numbers.")
    report.append("- Tokenizer mapping MathWriting->CROHME tokens is an approximation "
                  "(organizer caption conventions unverifiable offline); strict "
                  "exact-match is a lower bound, CER is the primary signal.")
    report.append("- 30 phone-photo-free samples: photo gap (perspective/lighting/blur) "
                  "NOT measured — needs authorized phone photos (future work).")
    out = os.path.join(HERE, "..", "reports", "inference_baseline.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print(f"exact={exact}/{n} meanCER={sum(cers)/n:.3f} oov_samples={oov_n}/{n} "
          f"meanLat={sum(lats)/n:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
