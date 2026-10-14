# PROJECT_STATE — Eigen

**Last updated:** `2026-10-14T08:12:31+05:30` (Recovery verification + second-commit session)

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

## Completed (Git baseline + Android readiness, 2026-10-13T13:59:48+05:30)

- Git: prior audit's "no commits, all untracked" confirmed still true (branch `main`,
  `git log` → "no commits yet"). Safety audit passed: `.gitignore` verified to exclude
  venvs (`backend/.venv`, `ml/.venv`), `mobile/node_modules`, `ml/checkpoints`,
  `ml/data`, real `.env` files (only `.env.example` ×2 tracked, placeholder content
  confirmed), caches, native builds, keystores — all via `git check-ignore`. Secret
  scan of staged diff clean (sole `keystore` hit = the `*.keystore` ignore rule
  itself). No file >1 MB among candidates (largest: `package-lock.json` 269 KB,
  `katexCss.ts` 24 KB). No `.gitignore` changes needed.
- Initial commit created: `5f45d5ac2d5bf9e0be0263f68ad7de5ba97f2bf0`
  `chore: establish Eigen project baseline` — 69 files, 12,625 insertions.
  Deliberately excluded (untracked, ignored): `backend/.venv`, `ml/.venv`,
  `mobile/node_modules`, `ml/checkpoints` (78.5 MB `best.ckpt`), `ml/data`
  (MathWriting excerpt). Working tree clean after commit.
- Android readiness (read-only checks, NOTHING installed/launched):
  Android Studio INSTALLED (`C:\Program Files\Android\Android Studio\bin\studio64.exe`);
  SDK present at `%LOCALAPPDATA%\Android\Sdk` (platform-tools, emulator 37.2.12.0,
  build-tools 36.0.0, platform android-37.0, google_apis_playstore x86_64 system
  image, licenses); AVD `Medium_Phone` (target android-37.0) EXISTS; adb 1.0.41
  works, `adb devices` → empty (no emulator running, no physical device).
  `ANDROID_HOME`/`ANDROID_SDK_ROOT` UNSET; `JAVA_HOME` = Adoptium JDK 21.0.8.9
  (suitable, 17+), but PATH `java` is still 1.8.0_401 (must not be used for builds).
  Expo side: `app.json` has CAMERA permission + adaptive icons + image-picker
  strings; NO `android.package`; NO `eas.json` (no EAS config).
- P3-VERIFY is NOT complete and Android is NOT claimed working — no emulator
  launched, no app run. Next action: launch the `Medium_Phone` AVD, then
  `npx expo start --android` from `mobile/` (emulator reaches host backend via
  `10.0.2.2:8000`, matching the client fallback).

## Completed (Recovery verification, 2026-10-14T08:12:31+05:30)

- Pre-existing working tree from the interrupted session verified WITHOUT
  re-running experiments: `run_posformer.py` CLI overrides (defaults =
  repo-exact, `BEAM` alias keeps `recognizer_worker.py` untouched);
  `posformer_run2_temp05.json` + `run2_summary.json` (T=0.5 vs T=1.0 on same
  30), `posformer_run3/4_l40_*.json` (40+40 with matching IDs, last 10
  unseen); `ml/reports/recognition_temp05.md` values match the JSONs
  (run1 mean CER 0.91195 → run2 0.85956; exact 0/40 both ways).
- Serving default VERIFIED UNCHANGED: `recognizer_worker.py` still uses
  repo-exact T=1.0 (file untouched — no diff); T=0.5 is experimental only.
- Tests 2026-10-14 (existing envs, no installs): backend `pytest` **34 passed
  + 1 skipped** (exit 0) + gated real-worker **1 passed** (10.59 s, exit 0);
  `ruff` clean; `ml/scripts/smoke_check.py` SMOKE OK (exit 0);
  `mobile` `npm run smoke` SMOKE OK (exit 0) + `tsc --noEmit` clean.
  New coverage: parser edge tests (`test_math_parser.py`),
  `test_security.py` (AST guard + HTTP injection/oversize/degenerate-solve),
  `anySignal()` fallback (`mobile/src/api/client.ts`), `mobile/tests/smoke.js`.
- Licensing re-verification (§10 in RESEARCH.md, KaTeX MIT header in
  `katexCss.ts`) reviewed as-is: accurate, no legal guarantees made.
- NO device/emulator run, NO EAS config, NO serving-default change, NO
  Phase 4 work. See CHANGELOG.md for exact commands and outcomes.

## Environment / dependency status

| Item | Status |
|---|---|
| Windows, Node 24.21.0, npm 11.19.0 | Verified working |
| Python 3.11.9, Git 2.53.0, OpenCode 1.18.35 | Verified working |
| NVIDIA RTX 4050 Laptop 6 GB, driver 592.82 / 16 GB RAM | Verified via `nvidia-smi` |
 | `backend/.venv` + pinned `requirements.txt` | FastAPI 0.118 + sympy/pillow/multipart; `pytest` 34+1 pass (2026-10-14) + gated real-worker 1 pass, `ruff` clean |
 | `ml/.venv` + harness | CPU torch 2.14.1; `best.ckpt` loaded via persistent worker (Phase 2, serving T=1.0 unchanged); `smoke_check.py` OK; T=0.5 experimental results recorded (run2/3/4, NOT deployed) |
 | `mobile/` + `package.json` + `package-lock.json` | Expo 57 six-screen MVP; `tsc --noEmit` clean, `npm run smoke` OK (katex/version/render/deps), `anySignal()` fallback for pre-`AbortSignal.any` runtimes; NO device run, NO EAS config |
 | Java on PATH (`java -version` → 1.8.0_401) | **Unsuitable** — must never be used for Gradle builds |
 | `JAVA_HOME` = Adoptium JDK 21.0.8.9 | Suitable (17+) — use for all Android/Gradle tooling (verified 2026-10-13) |
 | Android Studio | INSTALLED (verified 2026-10-13; was still downloading in Phase 0) |
 | Android SDK (`%LOCALAPPDATA%\Android\Sdk`) | Present: platform-tools (adb 1.0.41), emulator 37.2.12.0, build-tools 36.0.0, android-37.0, playstore x86_64 image, licenses |
 | `ANDROID_HOME` / `ANDROID_SDK_ROOT` | **Unset** (empty) — set before Gradle builds; Expo CLI auto-detects the default path |
 | Emulator / AVD | `Medium_Phone` (API 37.0) exists; NEVER launched; `adb devices` empty |
 | Expo Android config / EAS | `app.json` CAMERA permission + icons present; NO `android.package`, NO `eas.json` |
 | Git baseline | Commit `5f45d5a` (69 files) 2026-10-13; recovery verification 2026-10-14 green, second commit + GitHub push pending at time of writing |

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

## Blockers (as of 2026-10-13T13:59:48+05:30)

1. Android toolchain present but P3-VERIFY not started: Studio + SDK + `Medium_Phone`
   AVD exist (verified 2026-10-13), yet NO emulator has ever been launched and NO app
   run observed. Next action: launch AVD → `npx expo start --android` (backend via
   `10.0.2.2:8000`). `ANDROID_HOME` unset and no `android.package`/`eas.json` are
   minor gaps for later (Expo Go run needs neither).
2. PATH `java` is still 1.8.0_401 (trap for Gradle) → builds must use `JAVA_HOME`
   Adoptium JDK 21. Never put Java 8 on the build path.
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
