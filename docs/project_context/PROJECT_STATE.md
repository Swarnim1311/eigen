# PROJECT_STATE — Eigen

**Last updated:** `2026-10-13T13:29:00+05:30` (Phase 3 verification & close-out session)

## Objective

Cross-platform handwritten-mathematics recognition app: photograph handwritten math on
Android/iOS → recognition model returns LaTeX/symbols → restricted safe parser → SymPy
evaluation → result. Current phase: **Phase 3 mobile MVP IMPLEMENTED (code-complete,
2026-10-13 verified by inspection + automated checks, NOT device-tested). Phase 3 is
NOT fully verified — device/emulator runs, EAS config and automated mobile tests are
still pending (see Blockers).**

## Completed (Phase 0, 2026-10-09)

- Empty target dir confirmed; `git init` (branch `main`), root `.gitignore`, `README.md`, `AGENTS.md`.
- Repo skeleton: `mobile/`, `backend/app|tests`, `ml/{scripts,evaluation,experiments,reports}`,
  `docs/{project_context,architecture,decisions}`.
- Backend scaffold: `backend/pyproject.toml`, `requirements.txt` (pinned), `app/main.py`
  (`GET /health`, `GET /`), `tests/test_health.py`, `.env.example`.
- `backend/.venv` (Python 3.11.9, pip 24.0): FastAPI 0.118.0, Uvicorn 0.37.0,
  Pydantic 2.11.7, Pytest 8.3.5, HTTPX 0.28.1, Ruff 0.13.2 — all installed project-local.
- Expo blank-TypeScript scaffold moved into `mobile/` as `eigen-mobile` 0.1.0
  (Expo ~57.0.27, React 19.2.3, RN 0.86.3, TS ~6.0.3). Template `AGENTS.md`/`LICENSE`/`.claude`
  discarded; root docs govern.
- Research (web, primary sources, 2026-10-09): BTTR/CoMER/PosFormer/TAMER/CAN,
  pix2tex + restricted baselines, CROHME + MathWriting. See `RESEARCH.md`.

## Completed (Phase 1, 2026-10-09 → 2026-10-10)

- License re-verification from primary sources: PosFormer code = academic-only claim,
  still NO LICENSE file (raw 404); weights = no stated terms; BTTR code = MIT
  (verified text), weights = no stated terms; MathWriting excerpt = CC BY-NC-SA 4.0
  (eval use OK, commercial use not); official CROHME (TC11) unreachable from this
  machine + needs account (blocker documented, not bypassed).
- Isolated `ml/.venv` (Python 3.11.9, CPU torch 2.14.1, torchvision 0.29.1,
  einops 0.8.2, torchmetrics 1.9.0, opencv-headless 5.0.0.93, Pillow 12.3.0,
  numpy 2.4.6). Backend/mobile envs untouched.
- Downloaded ONLY: `best.ckpt` 78,508,976 B (sha256
  `943d3d28…818360ab71`, HEAD-verified before download; first attempt corrupt by
  concurrent writers — deleted, re-downloaded clean, torch.load OK) +
  MathWriting excerpt 1.6 MB (100 test inks used, 30 rendered for eval).
- GENUINE inference: released PosFormer weights, unmodified model code, repo's own
  preprocessing + beam search (10/200/1.0/no-early-stop/T=1.0), 750/750 state-dict
  keys loaded, 30 real predictions recorded in `ml/experiments/posformer_run1.json`,
  metrics in `ml/reports/inference_baseline.md`:
  exact-match 0/30, mean canonical CER 0.912, CPU latency mean 29.2 s/image.
- Polarity calibrated empirically: white-on-black renders decode (3.5 s, coherent);
  black-on-white run away to max_len garbage (712 s). CROHME polarity confirmed.
- Harness committed: `ml/scripts/{pl_compat,render_mathwriting,run_posformer,
  evaluate_baseline}.py` (+`ml/requirements.txt`, lock). Checkpoints/data/renders/
  venvs verified git-ignored. BTTR deliberately NOT run (primary succeeded; §4
  comparison recorded in RESEARCH.md).

## Completed (Phase 2, 2026-10-10)

- Safe math engine (`backend/app/math_parser.py`): recursive-descent parser for a
  documented grammar (integers/decimals, + - * / ^ **, parens, implicit `2x`/`2(x+1)`,
  unary minus, single `sqrt()`, variables {x,y,z,t}, one-`=` equations). NEVER
  eval/exec/sympify on input — SymPy built from validated tokens only. Limits:
  500 chars, 300 AST nodes, depth 100, 15-digit literals, |int exponent| ≤ 100.
  LaTeX subset translator (`\frac`, `\cdot`, `\times`, `\div`, `\left\right`).
- Endpoints (all Pydantic, structured `{error:{code,message}}`, no stack traces):
  `POST /api/v1/math/evaluate` (exact Rational + decimal), `/simplify`, `/solve`
  (univariate, allowlisted var, substitution-verified). Version → 0.2.0.
- Recognition API: `POST /api/v1/recognize` (upload validation: type/size
  ≤5 MB/dims 16–4000 px/format allowlist; in-memory only, never stored/logged)
  returns real `{latex, beam_score (uncalibrated), model+experimental flag,
  duration_s, math_parse status}`. `GET /api/v1/ready` reports
  ready/loading/standby/unavailable/unconfigured. Legacy `/health` + `/` unchanged.
- Integration without torch in backend env: ONE persistent stdio worker
  (`ml/scripts/recognizer_worker.py`, ml/.venv) holds the ckpt; backend
  `PosFormerWorkerService` (lazy singleton, lock, timeouts, restart budget,
  honest Unavailable fallback). No mocks, no per-request reload, no PosFormer
  source/checkpoint modification, no new downloads, no clearance claimed.
- Tests: 28 passed + 1 gated (real worker E2E passed separately in 38 s);
  ruff check + format clean; live uvicorn smoke (health/ready/evaluate) OK.
  Backend deps added: sympy 1.14.0, pillow 12.3.0, python-multipart 0.0.32.

## Completed (Phase 3 — mobile MVP, implemented before 2026-10-13; verification session 2026-10-13T13:29:00+05:30)

- Six-screen Expo Router flow, all code-inspected 2026-10-13: Home (`app/index.tsx`,
  recent-5 from SQLite + deep-link `history?open=`) → Capture (`app/capture.tsx`,
  camera/gallery via `expo-image-picker` only, `allowsEditing` system crop, client-side
  extension pre-check) → Recognize (`app/recognize.tsx`, multipart POST
  `/api/v1/recognize`, 180 s timeout, duplicate/stale guards, cancel keeps image,
  experimental-model warning) → Review (`app/review.tsx`, original prediction preserved,
  editable expression, KaTeX preview) → Result (`app/result.tsx`, evaluate/simplify/solve
  against real backend, conditional ops UI, auto-save on success) → History
  (`app/history.tsx`, list/detail/reopen/delete/clear-all, missing-file grace).
- API integration (`src/api/client.ts` + `src/api/types.ts` mirroring
  `backend/app/schemas.py`): `EXPO_PUBLIC_API_URL` → Expo host → `10.0.2.2:8000`
  resolution; validated responses; math 30 s / recognize 180 s timeouts; per-code hints.
- KaTeX/WebView rendering (`src/components/LatexView.tsx`): `katex.renderToString`
  (JS disabled, no remotes) + monospace fallback. DEFECT FOUND + FIXED 2026-10-13:
  stylesheet missing → bundled pinned `katex.min.css` verbatim as `src/components/katexCss.ts`;
  KaTeX webfonts still NOT bundled (system-serif fallback) and visual result is
  UNVERIFIED (no device/emulator available). See DECISIONS.md.
- SQLite history (`src/storage/history.ts`, `eigen.db`, schema v1, URI-only images,
  no server history). In-memory session (`src/state/session.ts`, deliberately
  non-persisted). System-crop-only: no custom preprocessing/rotation (documented
  in-file as out of scope — no dependable Expo Go library).
- DEFECT FOUND + FIXED 2026-10-13: `changed` flag in `app/review.tsx` false-positived
  on untouched drafts (compared against raw LaTeX as well as the ASCII draft source);
  now `draft !== session.corrected`. Logic proven via node probe (no mobile test
  framework exists — none introduced per phase constraints).
- Verification 2026-10-13 (see CHANGELOG.md): `npx tsc --noEmit` clean;
  `npx expo --version` 57.0.28; `npx expo-doctor` 19/21 (2 advisories, no action taken);
  backend `pytest tests` 28 passed + 1 skipped; live uvicorn smoke `/health` ok,
  `/api/v1/ready` standby (honest pre-load), `/math/evaluate` sqrt(16)+2^3 → 12.
  NO end-to-end run on any emulator, simulator, or physical device.

## Environment / dependency status

| Item | Status |
|---|---|
| Windows, Node 24.21.0, npm 11.19.0 | Verified working |
| Python 3.11.9, Git 2.53.0, OpenCode 1.18.35 | Verified working |
| NVIDIA RTX 4050 Laptop 6 GB, driver 592.82 / 16 GB RAM | Verified via `nvidia-smi` |
| `backend/.venv` + pinned `requirements.txt` | FastAPI 0.118 + sympy/pillow/multipart; `pytest` 28+1 pass, `ruff` clean |
| `ml/.venv` + harness | CPU torch 2.14.1; `best.ckpt` loaded via persistent worker (Phase 2) |
 | `mobile/` + `package.json` + `package-lock.json` | Expo 57 six-screen MVP; `tsc --noEmit` clean, `expo --version` 57.0.28, `expo-doctor` 19/21 (react-duplicate + expo/expo-router patch advisories); NO device run, NO automated mobile tests, NO EAS config |
| Java 1.8.0_401 on PATH | **Unsuitable** for current Android/Gradle; use Studio-bundled JDK 17+ |
| `ANDROID_HOME` / SDK | **Absent** — Android Studio still downloading |
| PyTorch / checkpoints / datasets | `ml/.venv` CPU torch 2.14.1; `best.ckpt` verified+loaded; MathWriting excerpt eval-only |
| `ANDROID_HOME` / SDK | **Absent** — recheck pending (was still downloading in Phase 0) |

## Implemented vs unimplemented (as of 2026-10-13)

- Implemented: repo skeleton, backend health endpoint, docs context system, research
  reports, standalone HMER harness + 30-sample baseline, **recognition API + safe math
  engine (tested)**, **six-screen mobile MVP (Home/Capture/Recognize/Review/Result/
  History) with API client, KaTeX/WebView preview (CSS bundled 2026-10-13, fonts
  fallback), local SQLite history, in-memory session (all code-inspected; automated
  checks green)**.
- Implemented but UNVERIFIED: everything requiring a running app — camera/gallery
  pickers, upload over network, rendered LaTeX appearance, SQLite on-device behavior,
  navigation flow end-to-end. (`tsc` + backend tests do NOT cover these.)
- NOT implemented (by design / pending): camera preprocessing beyond the system crop
  editor, automated mobile tests (no framework chosen), EAS configuration,
  physical-device or emulator builds/runs, server-side history, fine-tuning, signing,
  deployment.

## Blockers (as of 2026-10-13T13:29:00+05:30)

1. Android Studio/SDK status unchanged/unchecked → no emulator/ADB validation.
   **This is now THE gating blocker: it prevents any end-to-end verification of the
   Phase 3 mobile MVP (camera, upload, render, SQLite on-device).**
2. Java 8 on PATH is a trap for future Gradle builds → must use Studio-bundled JDK 17+.
3. No checkpoint/dataset cleared for COMMERCIAL use or redistribution (PosFormer
   academic-only/ambiguous, BTTR weights unstated, all datasets NC). Research/eval
   use is fine; product use needs legal clearance + permissive data. **Unresolved.**
4. iOS Simulator impossible on Windows → physical iPhone + EAS only. **No iPhone test
   performed; no EAS configuration exists.**
5. Official CROHME access needs TC11 account (user action); worked around with the
   public MathWriting excerpt for Phase 1. No authorized phone photos yet → photo
   gap unmeasured.
6. CPU inference ~29 s/image — interactive use needs GPU torch + batching (Phase 2+).
7. No automated mobile tests (no framework selected — deliberately not introduced in
   Phase 3). No camera preprocessing beyond the OS crop editor. KaTeX webfonts not
   bundled → rendered-glyph fidelity unverified even after the 2026-10-13 CSS fix.
