# Recognition decoding experiment — temperature 0.5 vs repo default 1.0

**Date:** `2026-10-13` (session timestamp in CHANGELOG.md).
**Question:** does sharpening the beam-search softmax improve the PosFormer
baseline without touching model, data, or preprocessing?

## Verification first (no bugs found)

- Preprocessing = repo training path exactly: `ScaleToLimitRange(16..1024,
  16..256)` + `ToTensor`, no normalization (`dataset.py` confirmed).
- Mask convention = repo `collate_fn`: `1` = pad, `0` = content; harness feeds an
  unpadded image with all-zeros mask (all content). Correct.
- Decoding = repo's own bidirectional `beam_search` with `config.yaml` values
  (beam 10 / max_len 200 / alpha 1.0 / no early stop / T 1.0). The repo's own
  `test_step` also calls raw `indices2label` with no SOS/EOS stripping, so the
  `<sos>` leak in sample `0017bb5822bcba69` is upstream behavior, not a harness
  bug. No pipeline fix was justified.
- Evaluator (`evaluate_baseline.py` `canon`/`lev`/`tokenize_gt`) re-used verbatim
  via import for all numbers below — same procedure as `inference_baseline.md`.

## Method (leakage-controlled)

1. Reproduced 3 samples with repo settings → predictions byte-identical to
   `posformer_run1.json` (`experiments/posformer_repro_check.json`). Pipeline
   deterministic; baseline still holds.
2. Added `--beam-size/--max-len/--alpha/--early-stopping/--temperature` CLI
   overrides to `run_posformer.py` (defaults = repo values; `rp.BEAM` alias kept
   so `recognizer_worker.py` is untouched and still repo-exact).
3. Tuned ONE setting (T=0.5) on the original 30 samples → `posformer_run2_temp05.json`.
4. Confirmed on 10 unseen samples (rows 31–40): fresh T=1.0 run
   (`posformer_run3_l40_t10.json`) vs fresh T=0.5 run (`posformer_run4_l40_t05.json`).

## Results (same 30 samples, same eval code)

| run | exact | mean CER | median CER | latency mean (min–max) |
|---|---|---|---|---|
| run1 T=1.0 (baseline) | 0/30 | 0.912 | 0.838 | 29.2 s (5.9–88.0) |
| run2 T=0.5 | 0/30 | **0.860** | 0.867 | **7.1 s (1.7–19.8)** |

Per-sample (30): 8 better, 15 unchanged, 7 worse. Fixes the `x`→`X` case error
(`000a4e8ca49c5a1c` CER 0.769→0.385) and the `<sos>` leak (`0017bb5822bcba69`
1.444→1.000). Worst regressions ≤ +0.09 CER.

Unseen rows 31–40: T=1.0 mean 0.977 vs T=0.5 mean **0.909** (2 better / 3 worse /
5 same). Direction consistent → the gain is not tuning-split luck.
All-40: 0.928 → 0.872, exact still 0/40 both ways.

## Decision

- T=0.5 is a **modest, reproducible win**: −0.05 mean CER, ~4× faster (shorter,
  less loopy outputs), generalizes beyond the tuning split.
- It is NOT production readiness: exact-match stays 0/40; `|` collapse, case
  confusion and runaway loops persist on hard samples — the CROHME→MathWriting
  render-style domain gap dominates (in-vocab-11 subset CER 0.922 ≈ full set).
- Live default UNCHANGED: `recognizer_worker.py` still uses repo-exact T=1.0
  (avoid tuning the serving path on n=40 evidence). To enable for demo use, set
  the worker call to `temperature=0.5` — one line, reversible; re-run the gated
  E2E after any such change.
- Next accuracy levers (not executed): GPU torch for iteration speed → evaluate
  on CROHME-style renders / organizer test sets; vocab extension + small
  fine-tune on MathWriting (needs license clearance + data, see DECISIONS.md).

## Artifacts

- `experiments/posformer_run2_temp05.json` (30, T=0.5),
  `posformer_run3_l40_t10.json` + `posformer_run4_l40_t05.json` (40+40),
  `posformer_run2_summary.json` (aggregate only).
- `posformer_repro_check.json` / `posformer_temp05_check.json`: superseded
  3-sample pilots, kept for provenance.
