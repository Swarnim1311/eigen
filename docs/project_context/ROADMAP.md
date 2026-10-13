# ROADMAP — Eigen

**Last updated:** `2026-10-13T13:29:00+05:30` (Phase 3 verification & close-out)

## Phase 0 — Foundation + research ✅ COMPLETE (2026-10-09)

Acceptance (all met or explicitly deferred with reason):
- [x] Dir/gitignore/README/AGENTS.md/context docs created, existing work preserved (dir was empty).
- [x] `backend/.venv` works; `pytest` 2/2 pass; `ruff` clean; live `/health` OK.
- [x] `mobile/` Expo 57 TS scaffold; `tsc --noEmit` clean; `expo --version` 57.0.28.
- [x] Manifests pinned (`requirements.txt`, `package.json` + `package-lock.json`).
- [x] Research with primary-source links + license verification status (`RESEARCH.md`).
- [x] Implemented vs proposed distinguished; blockers reported, not hidden.
- [ ] Android SDK validation — BLOCKED (Studio still downloading), reported.

## Phase 1 — License review + reproducible inference ✅ COMPLETE (outcome A, 2026-10-10)

- [x] License re-verified from primary sources (code/weights/data/commercial split).
- [x] Standalone `ml/.venv` + manifests (`ml/requirements.txt`, lock).
- [x] Released ckpt downloaded minimally (78.5 MB only) + hash recorded.
- [x] 30-sample genuine inference with recorded predictions + metrics
      (`ml/experiments/posformer_run1.json`, `ml/reports/inference_baseline.md`).
- [x] BTTR fallback assessed without execution (documented rationale).
- [ ] CROHME official access — BLOCKED (TC11 account needed: user creates account at
      tc11.cvc.uab.es, accepts terms, downloads `TC11_package_CROHME2019.zip`).
- [ ] 5 phone photos — NONE available (user to supply authorized photos later).
- [ ] Maintainer contact for weight redistribution — NOT done (needs authorization).

## Phase 2 — Backend recognition API + safe SymPy eval ✅ COMPLETE (2026-10-10)

- [x] `POST /api/v1/recognize` via replaceable interface + persistent worker
      (real predictions; honest unavailable/error paths; no mocks).
- [x] Restricted parser + `/math/evaluate|/simplify|/solve` (tested incl.
      injection, div-zero, limits).
- [x] `/health` intact; `/api/v1/ready` added (ready/loading/standby/...).
- [x] 28 passed + 1 gated E2E passed; ruff clean; live uvicorn smoke OK.
- [x] No SQLite history (deferred by design); no new model/dataset downloads.

## Phase 3 — Mobile capture → result flow (Expo Router) — IMPLEMENTED, PARTIALLY VERIFIED (2026-10-13)

Implemented (code-inspected + automated checks green, see PROJECT_STATE.md / CHANGELOG.md):
- [x] Six screens: Home → Capture → Recognize → Review → Result → History.
- [x] Camera/gallery selection (`expo-image-picker`, system crop UI only — no custom
  preprocessing, by decision), client-side image pre-check, multipart upload with
  180 s timeout, per-code error hints, cancel/duplicate/stale guards.
- [x] Evaluate/simplify/solve against the real backend (conditional ops UI), auto-save
  to local SQLite history on success; history list/detail/reopen/delete/clear-all.
- [x] KaTeX/WebView LaTeX preview with fallback (stylesheet bundled 2026-10-13;
  webfonts still system-fallback).
- [x] `tsc --noEmit` clean; backend `pytest` 28+1 green; `/health` + `/ready` +
  `/math/evaluate` smoke OK.

Still pending — Phase 3 may NOT be called complete until these are done:
- [ ] End-to-end run on an Android emulator/device (BLOCKED: Android SDK unchecked/absent).
- [ ] iPhone physical test via dev/EAS build (BLOCKED: no device access, no EAS config).
- [ ] EAS configuration (deliberately not introduced in this phase).
- [ ] Automated mobile tests (no framework selected; none introduced in this phase).
- [ ] Camera preprocessing beyond the OS crop editor (out of scope by decision).
- [ ] Visual confirmation of KaTeX rendering (CSS fix is code-verified only).

## Phase 4 — Baseline + fine-tune experiments

- Restricted baseline (CRNN+CTC or CNN-LSTM) on simple expressions; small fine-tune of
  Phase-1 model on MathWriting subset if metrics justify; eval reports in `ml/reports/`.
- Depends on: Phases 1–3 metrics.

## Blocked / parked

- Device testing (Android emulator, iPhone) — parked until Phase 3 + SDK/hardware ready.
- Production signing, subscriptions, public infra — explicitly out of scope until later.
