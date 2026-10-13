# CHANGELOG — Eigen

## 2026-10-13T13:29:00+05:30 — Phase 3 verification & close-out (build mode)

Scope: verify + document the pre-existing mobile MVP. No rebuild, no new/EAS/mobile-test
deps installed or upgraded, no backend behavior changed, nothing committed.

Commands run (from `C:\Users\Swarnim\Desktop\ML projects\eigen`) and actual results:
- `npx tsc --noEmit` (mobile/) → clean, exit 0 (also clean AFTER the two fixes below).
- `npx expo --version` (mobile/) → 57.0.28.
- `npx expo-doctor` (mobile/, no installs) → 19/21 checks passed; 2 advisories:
  duplicate `react` (19.2.3 nested vs 19.1.1 hoisted) + `expo ~57.0.28` vs 57.0.27 /
  `expo-router ~57.0.26` vs 57.0.25 patch mismatches. Reported, not acted on.
- `.\.venv\Scripts\python.exe -m pytest tests -q` (backend/) → 28 passed, 1 skipped
  (gated), 1 warning (starlette BlockingPortal deprecation, upstream/harmless), 1.85 s.
- Live uvicorn smoke (port 8124, existing startup procedure):
  `GET /health` → `{"status":"ok","service":"eigen-backend"}`;
  `GET /api/v1/ready` → `{"api":"ok","model":{"status":"standby",...}}` (honest pre-load);
  `POST /api/v1/math/evaluate {"expression":"sqrt(16)+2^3"}` → `{"result":"12",...}`.

Code inspected (all, no rewrites): `mobile/app/` ×6 routes + `_layout.tsx`,
`src/api/{client,types}.ts`, `src/components/{LatexView,ui}.tsx`,
`src/state/session.ts`, `src/storage/history.ts`, `src/utils/validate.ts`,
`src/theme/tokens.ts`. Automated-check coverage: `tsc` only. Smoke-tested: backend
endpoints only. Verified on device/emulator: NOTHING (no SDK, no device).

Fixes made (the two sanctioned suspects only):
- `mobile/src/components/LatexView.tsx` (+ new `src/components/katexCss.ts`):
  KaTeX HTML used layout classes with no stylesheet shipped → inlined pinned
  `katex.min.css` (23,352 B, verbatim, JSON-escaped by generator; regen on katex
  upgrade) ahead of app overrides. Fonts intentionally still unbundeled (offline
  WebView fallback). `tsc` clean; node probe asserts `.mfrac`/`.vlist` rules present.
  Visual result UNVERIFIED — not claimed fixed, see DECISIONS.md §18.
- `mobile/app/review.tsx`: `changed` compared draft against raw LaTeX too, so every
  untouched draft with an ASCII conversion showed "You edited…" → now
  `draft !== session.corrected`. Proven via throwaway node probe (old=true/new=false
  on untouched draft; both true after edit). No test framework exists under
  `mobile/tests/` (only `.gitkeep`) — none introduced.

Docs updated: PROJECT_STATE.md, ROADMAP.md (duplicate/stale Phase 3 sections merged
into one IMPLEMENTED/PARTIALLY-VERIFIED entry), ARCHITECTURE.md (blank-scaffold and
no-mobile-traffic statements corrected), DECISIONS.md (§17–21), CHANGELOG.md (this
entry), README.md (mobile description + quick-start phase label).

## 2026-10-10T08:58:00+05:30 — Phase 2 session (build mode)

New backend deps (pinned in `backend/requirements.txt`, installed project-local):
sympy 1.14.0, pillow 12.3.0, python-multipart 0.0.32.

Files created:
- `backend/app/math_parser.py` (grammar, limits, latex subset, evaluate/simplify/solve)
- `backend/app/schemas.py`, `backend/app/recognizer.py` (service + worker client),
  `backend/app/routers/{__init__,math_router,recognize_router}.py`
- `ml/scripts/recognizer_worker.py` (persistent stdio inference worker)
- `backend/tests/{test_math_parser,test_math_api,test_recognize}.py`
Rewrote `backend/app/main.py` (routers, lifespan, structured error handlers,
version 0.2.0); extended `backend/.env.example` (EIGEN_* worker paths).

Defects found by tests and fixed: solve test used wrong expected value
(2x+3=7 → x=2, not 5/2); JSON floats coerce to Float → integral floats now
restored to int in evaluate(); stray raises-block in limits test; FastAPI
Union return annotation → response_model=None; worker stdout logs broke the
readiness handshake → protocol skips non-JSON lines; handshake space-strip
mismatch; blocking pipe reads → executor timeouts (300 s load / 600 s req).

Tests run: `pytest tests` → 28 passed, 1 skipped (gated); with
EIGEN_TEST_WORKER=1 → real worker E2E passed in 38.3 s (spawn + load +
inference on Phase-1 render, non-empty LaTeX, status ready).
`ruff check` clean; `ruff format` applied (9 files). Live uvicorn smoke:
`/health` ok, `/ready` standby (honest pre-load), `/math/evaluate`
sqrt(16)+2^3 → 12. No mobile/ML-env/PosFormer-source changes; no new downloads.

## 2026-10-10T08:50:00+05:30 — Phase 1 session (build mode)

License re-verification (primary sources, 2026-10-09/10):
- PosFormer README re-fetched: academic-only + BSD-2 claim, TODO LICENSE still open;
  `LICENSE` raw URL → 404 (still absent) — Verified.
- BTTR `LICENSE` raw → MIT text (1068 B) — Verified; v2.0 release page confirms
  `pretrained-2014` asset — Verified.
- HEAD checks (no downloads): PosFormer `best.ckpt` 200/78,508,976 B; BTTR ckpt
  200/77,545,147 B; MathWriting excerpt 200/1,620,634 B; CoMER `data.zip`
  200/30,894,119 B (not used); TC11 site connection failure (official CROHME blocked).
- GitHub API 403 rate-limited → used raw/HEAD checks instead.

ML env (`ml/.venv`, isolated, py3.11.9): torch 2.14.1+cpu, torchvision 0.29.1+cpu,
pillow 12.3.0, numpy 2.4.6, einops 0.8.2, torchmetrics 1.9.0,
opencv-python-headless 5.0.0.93 (freeze: `ml/requirements.lock.txt`).

Downloads (minimal, justified): `best.ckpt` → `ml/checkpoints/` (first attempt
corrupt via concurrent writers: deleted; clean single-stream re-download
78,508,976 B, sha256 `943d3d28c7302a2153bfeba87958b2fb48718b55d39b6a8eed234a818360ab71`,
torch.load OK, epoch 206, 750 `model.*` tensors); MathWriting excerpt 1.6 MB →
`ml/data/` (100 test inks). PosFormer code: sparse blobless clone to scratch
`%TEMP%/opencode/PosFormer-code` (outside repo, not committed).

Files created: `ml/scripts/pl_compat.py` (PL shim + unpickle finder),
`render_mathwriting.py` (InkML→PNG both polarities, 100 samples + labels.tsv),
`run_posformer.py` (plain-torch beam-search harness), `evaluate_baseline.py`
(canonical CER + token exact-match + OOV analysis); `ml/requirements.txt`;
`ml/experiments/posformer_run1.json` (30 predictions); `ml/reports/inference_baseline.md`.
`pl_compat` gained callbacks submodule + generic `_PLFinder` after two unpickle
`ModuleNotFoundError`s; `evaluate_baseline` fixed `sqrt`→double-backslash mapping bug.

Commands executed (key): `python -m venv ml\.venv`; pip installs (cpu index);
`render_mathwriting.py test` → 100 samples × 2 polarities; smoke run
(`--random-weights`, 324 s, garbage as expected); calibration 1 sample × 2
polarities (black-bg 3.5 s coherent vs white-bg 712 s runaway → polarity = white
ink on black); full run `--limit 30` → 879.5 s total; `evaluate_baseline.py`.

Tests/results: ckpt load 750/750 keys, missing=0; 30 genuine predictions recorded;
exact 0/30, mean CER 0.912 (median 0.838), in-vocab-11 CER 0.922, latency mean
29.2 s (5.9–88.0 s) CPU. No backend/mobile code touched (envs verified intact).
No weights/data/venvs committed (check-ignore verified). BTTR not run (rationale
in DECISIONS.md). No phone photos (none available). No fine-tuning (out of scope).

## 2026-10-09T21:35:00+05:30 — Phase 0 session (build mode)

Environment verified:
- `node --version` → v24.21.0; `npm --version` → 11.19.0
- `python --version` → Python 3.11.9; system pip 26.2.1; venv pip 24.0
- `git --version` → 2.53.0.windows.1; `opencode --version` → 1.18.35
- `java -version` → 1.8.0_401 (unsuitable for current Android builds)
- `ANDROID_HOME`/`ANDROID_SDK_ROOT` empty; no SDK under `%LOCALAPPDATA%\Android\Sdk`
- `nvidia-smi` → RTX 4050 Laptop 6 GB, driver 592.82
- npm registry reachable: `expo` 57.0.27, `expo-router` 57.0.25, CLI 5.0.3

Files created:
- `.gitignore`, `README.md`, `AGENTS.md`
- `backend/pyproject.toml`, `backend/requirements.txt`, `backend/.env.example`
- `backend/app/__init__.py`, `backend/app/main.py`, `backend/tests/__init__.py`,
  `backend/tests/test_health.py`
- `mobile/package.json`, `mobile/app.json` (as `eigen-mobile` 0.1.0),
  moved `App.tsx`, `index.ts`, `tsconfig.json`, `assets/`, `package-lock.json`,
  `node_modules/` from `mobile-tmp/` scaffold; added `mobile/src/`, `mobile/tests/`
- `docs/project_context/` × 6 (this set)

Dependencies installed (project-local only):
- `python -m venv backend\.venv` → OK
- `backend\.venv\Scripts\pip.exe install -r backend\requirements.txt` → OK:
  fastapi 0.118.0, uvicorn 0.37.0, pydantic 2.11.7, pytest 8.3.5, httpx 0.28.1,
  ruff 0.13.2 (+ starlette 0.48.0, anyio 4.15.1)
- `npx create-expo-app@latest mobile-tmp --template blank-typescript` → OK
  (expo ~57.0.27, react 19.2.3, react-native 0.86.3, typescript ~6.0.3);
  `mobile-tmp/` merged into `mobile/`, tmp dir removed. Template AGENTS.md/LICENSE/
  .gitignore/.claude discarded.

Commands executed (all in `C:\Users\Swarnim\Desktop\ML projects\eigen` unless noted):
- `git init; git branch -M main`
- `python -m venv backend\.venv`
- `pip install -r backend\requirements.txt` (inside venv)
- `python -m pytest backend\tests -q` (from root)
- `ruff check backend\`; `ruff format --check backend\app backend\tests`
- uvicorn live check (port 8124, in-process): `GET /health` → `{"status":"ok",...}`
- `npx tsc --noEmit` (mobile/) — clean; `npx expo --version` → 57.0.28
- Research via web search + official repo/doc fetches (2026-10-09), 3 parallel tracks:
  BTTR-family, pix2tex+baselines, CROHME+MathWriting. No checkpoints/datasets downloaded.

Tests run and outcomes:
- `pytest backend\tests -q` → **2 passed** (test_health_ok, test_root_points_to_health);
  one starlette `BlockingPortal` deprecation warning (upstream, harmless).
- `ruff check` → all checks passed; `ruff format --check` → 4 files already formatted.
- Live `/health` via uvicorn → 200 `{"status":"ok","service":"eigen-backend"}`.
- `tsc --noEmit` (mobile) → clean, no errors.
- Device tests (Android emulator / iPhone) → NOT run (SDK absent / hardware N/A).
- Model inference → NOT run (no downloads per Phase 0 scope).
