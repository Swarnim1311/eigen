# ARCHITECTURE — Eigen

**Last updated:** `2026-10-14T08:12:31+05:30` (Recovery verification recorded)

## Current (actually implemented) architecture

```text
mobile/eigen-mobile (Expo 57, Expo Router, TypeScript strict)
  app/ (6 routes): index (Home: brand, scan/import, recent-5, history link)
    -> capture (expo-image-picker camera/gallery + allowsEditing system crop
       + extension pre-check, image review, session seed)
    -> recognize (multipart POST /api/v1/recognize, 180 s timeout,
       duplicate/stale/cancel guards, experimental-model warning)
    -> review (original LaTeX preserved, editable expression, KaTeX preview)
    -> result (evaluate/simplify/solve, conditional ops UI, auto-save)
    -> history (SQLite list/detail/reopen/delete/clear-all, missing-file grace)
  src/api/ (client.ts: EXPO_PUBLIC_API_URL -> Expo host -> 10.0.2.2:8000;
    validated responses; math 30 s timeout; per-code hints;
    anySignal() fallback for runtimes without native AbortSignal.any)
  src/components/LatexView.tsx (katex.renderToString -> offline WebView,
    JS disabled, no remotes; pinned katex.min.css bundled verbatim as
    katexCss.ts since 2026-10-13; webfonts NOT bundled -> serif fallback;
    monospace fallback on unsupported LaTeX)
  src/storage/history.ts (expo-sqlite eigen.db, schema v1, URI-only images)
  src/state/session.ts (in-memory working session, deliberately non-persisted)

backend/ (FastAPI 0.118, Python 3.11 venv)
  GET /         -> {"service","health"}
  GET /health   -> {"status":"ok","service":"eigen-backend"}
   POST /api/v1/recognize + /api/v1/math/* + GET /api/v1/ready (v0.2.0, Phase 2)
   tests/ (34 passed + 1 skipped + 1 gated real-worker, 2026-10-14 re-verified;
     includes test_security.py AST+HTTP guards)

 ml/             -> Phase-1 standalone harness: scripts/ (pl_compat, render,
   run_posformer --beam-size/--max-len/--alpha/--early-stopping/--temperature
   CLI overrides, defaults repo-exact, 2026-10-13, evaluate_baseline,
   smoke_check.py offline checks) + Phase-2 recognizer_worker.py (persistent
   stdio inference server, loads best.ckpt once, STILL repo-exact T=1.0 —
   serving default unchanged by decision §22), requirements.txt + lock,
   checkpoints/ (git-ignored), data/ (git-ignored),
   experiments/posformer_run1.json + run2_temp05/run3_l40_t10/run4_l40_t05 +
   run2_summary.json, reports/inference_baseline.md + recognition_temp05.md
   (T=0.5 experimental: 0.912 -> 0.860 mean CER on same 30, 0/40 exact both —
   NOT deployed)
docs/           -> context system (this file set) + empty architecture//decisions/ stubs
```

Backend serves recognition through the worker (lazy singleton, sequential lock,
timeouts, restart budget); math endpoints are pure backend (no ML dependency).
Mobile↔backend client code is COMPLETE (typed client, validated responses,
documented URL/timeout strategy) but has NEVER run against a live backend from a
real app instance — no emulator/device execution yet. ML inference path exists
server-side (Phase 2 worker); mobile exercises it only via `/recognize`.

## Live endpoints (v0.2.0, all verified 2026-10-10)

```text
GET  /health               -> {"status":"ok",...} (unchanged since Phase 0)
GET  /                     -> service pointer (unchanged)
POST /api/v1/math/evaluate -> {result (exact), decimal|null, expression}
POST /api/v1/math/simplify -> {result, expression}
POST /api/v1/math/solve    -> {variable, solutions[], count}
POST /api/v1/recognize     -> {latex, beam_score, model{experimental}, duration_s,
                               math_parse{ok, ascii?}}  (multipart image upload)
GET  /api/v1/ready         -> {api, model{status, detail}}
Errors                     -> {error:{code, message}} (400/413/415/422/502/503)
```

No mobile↔backend traffic has been OBSERVED yet (no app execution on any
device/emulator); the client code path is complete but unexercised end-to-end.

## Proposed (target) architecture

```text
[Phone camera] -> [Expo app: capture/crop/preprocess, SQLite cache]
      | HTTPS JSON (multipart image upload / LaTeX+result response)
      v
[FastAPI] -> [restricted parser] -> [SymPy] -> result
      |
      +-> [PyTorch HMER model service] (initial: PosFormer or TAMER checkpoint;
          fallback: BTTR; comparison: pix2tex; baseline: CNN-RNN/CRNN+CTC)
      +-> [SQLite persistence, eval logs]
```

## Component responsibilities (target)

- Mobile: image capture, crop/deskew/contrast, upload, render LaTeX, show steps/result,
  offline SQLite cache. Must stay Expo-SDK-compatible and platform-agnostic.
- Backend: auth (later), `/recognize` + `/evaluate` endpoints, file validation/size limits,
  restricted math parser (allowlist only — never raw `eval`/`sympify`), SymPy execution
  with timeouts, model inference wrapper, SQLite logging.
- ML service (inside or beside backend, TBD Phase 1): checkpoint loading, preprocessing
  identical to training rasterization, beam search decode, confidence + fallback to
  restricted baseline on low confidence.

## Data flow (target)

`photo -> preprocess -> POST /recognize -> HMER image→LaTeX -> restricted parse ->
SymPy -> {latex, result, confidence} -> app render + SQLite`.

## Proposed vs implemented

| Concern | Proposed | Implemented (2026-10-13) |
|---|---|---|
| Mobile screens/router | Expo Router flows | 6-route flow Home/Capture/Recognize/Review/Result/History (code-complete, never executed) |
| Backend API | recognize/evaluate | `/health` + `/` + `/api/v1/math/*` + `/api/v1/recognize` + `/api/v1/ready` (tested) |
| Mobile↔backend | HTTPS JSON upload/LaTeX | Typed client + validation + timeouts (code-complete, no live run) |
| Math eval | Restricted parser + SymPy | Token-built SymPy, grammar+limits documented in math_parser.py |
| LaTeX render | Render + show result | KaTeX static HTML in offline WebView; katex.min.css bundled, fonts fallback, monospace fallback (appearance unverified) |
| Image capture/crop | capture/crop/preprocess | System picker + OS crop editor only; no custom preprocessing (decision) |
| Persistence | SQLite | Local `eigen.db` history (code-complete, on-device behavior unverified); no server history |
| Model | PosFormer/TAMER (+fallback) | PosFormer via persistent worker; replaceable RecognizerService interface |

## Key constraints recorded

- 6 GB VRAM / 16 GB RAM → small checkpoints, batch 4–8, fp16, no large-VLM fine-tuning.
- Windows dev: Android via Studio/emulator/device; iOS via physical iPhone + EAS cloud only.
- External device testing needs remotely reachable HTTPS backend (later phase).
