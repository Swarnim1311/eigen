# DECISIONS — Eigen

## 2026-10-13T13:29:00+05:30 — Phase 3 verification choices

17. **System crop editor ONLY (`allowsEditing`); no custom camera preprocessing or
    rotation UI.** Reason: no dependable cross-platform Expo Go library for
    deskew/rotate exists in this SDK; custom native code would break Expo Go +
    platform-agnosticism. Consequence: crop quality depends on the OS editor;
    preprocessing stays a pending item, not a silent gap.
18. **LaTeX via `katex.renderToString` into an offline WebView (JS disabled, no
    remote/file access), with a monospace source fallback — never a crash on bad
    model output.** Reason: pure-JS rendering keeps Expo Go compatibility; the
    lockdown makes untrusted LaTeX inert. Consequence: verified 2026-10-13 that the
    KaTeX stylesheet was MISSING (unstyled fractions/roots) → bundled pinned
    `katex.min.css` verbatim as `src/components/katexCss.ts` (regenerate on katex
    upgrade). KaTeX webfonts deliberately NOT bundled (base64 would bloat the
    bundle; offline WebView cannot resolve font files) → system-serif fallback.
    Visual result UNVERIFIED (no device/emulator) — must be eyeballed before any
    "rendering works" claim.
19. **Review `changed` = `draft !== session.corrected` (fixed 2026-10-13).** The old
    `draft !== originalLatex || ...` false-positived on every untouched draft whose
    ASCII conversion differed from the raw LaTeX (the common case). Proven with a
    throwaway node probe; no mobile test framework introduced (none exists in
    `mobile/tests/` — selection deferred).
20. **In-memory session (`src/state/session.ts`) + local SQLite history
    (`eigen.db`, schema v1, image URIs only).** Reason: router params stay tiny;
    a killed app restarts cleanly from Home/History; no accounts, no server-side
    image/expression storage. Consequence: history is per-device, unmigrated
    schema changes must go through `PRAGMA user_version` migrations.
21. **API URL: `EXPO_PUBLIC_API_URL` → Expo dev host → `10.0.2.2:8000`; math 30 s,
    recognize 180 s timeouts (CPU baseline ~29 s avg, ~90 s peak).** Reason: a phone
    cannot reach host `localhost`; baked-in `EXPO_PUBLIC_*` must never carry
    production secrets. Consequence: physical-device runs need the LAN-address
    procedure in README.md; production HTTPS base URL still undecided.

## 2026-10-10T08:58:00+05:30 — Phase 2 choices

13. **Recognizer behind `RecognizerService` protocol, served by ONE persistent
    stdio worker in ml/.venv — no torch in backend env.** Alternatives: torch in
    backend/.venv (breaks env separation), per-request subprocess (reloads 78 MB
    ckpt each call — explicitly forbidden), HTTP microservice (heavier ops).
    Reason: keeps envs separate, loads ckpt once, returns REAL predictions.
    Consequence: sequential inference (lock), CPU ~30 s/req, worker lifecycle to
    operate. Swap cost for a future model = new protocol implementation.
14. **Hand-written recursive-descent math grammar; SymPy built from validated
    tokens; no eval/exec/sympify on input.** Reason: model/latex input is
    untrusted; only token-constructed Integer/Rational/Symbol/Add/Mul/Pow/sqrt
    can exist. Consequence: narrow v1 grammar ({x,y,z,t}, sqrt() only,
    no functions/matrices) — rejections are the safe default.
15. **No server-side history/SQLite in Phase 2.** Reason: no product requirement;
    history belongs to the mobile app (local). Backend logs operations only
    (sizes/durations), never image bytes or expression content beyond errors.
16. **Beam score exposed as uncalibrated `beam_score`, never a confidence.**
    Reason: task forbids fabricated confidence; the score is a real search score
    but not a probability. `experimental:true` + baseline note on every response.

## 2026-10-10T08:50:00+05:30 — Phase 1 choices

8. **Isolated `ml/.venv` (py3.11) with MODERN CPU torch 2.14.1 instead of the
   repo-pinned torch 1.8.1/py3.7.** Alternatives: conda py3.7 + torch 1.8.1 (no
   cp311 wheels exist → dead end), system-wide install (rejected). Reason: only
   inference needed; model code is plain nn.Modules. Consequence: `ml/requirements.txt`
   + lock record modern equivalents; fine-tune path may still need legacy env —
   revisit with evidence.
9. **Lightning-free harness (`ml/scripts/pl_compat.py` shim) instead of installing
   pytorch-lightning.** Reason: inference uses only `nn.Module` + `.device`;
   installing PL 1.4.9 is impossible on py3.11 and PL 2.x API differs (`gpus=1`
   removed). The shim fabricates unpickle stubs for `pytorch_lightning.*` and
   refuses training use. Consequence: PosFormer source UNMODIFIED (lives in scratch
   dir, outside repo); all compat surface is one documented 100-line file.
10. **Samples = MathWriting excerpt test inks (100 available, 30 used), NOT CROHME.**
    Reason: excerpt is officially public (GCS, 1.6 MB, CC BY-NC-SA eval OK);
    TC11 unreachable + account-walled; CoMER `data.zip` provenance murky.
    Consequence: baseline is cross-dataset (CROHME-trained → MathWriting renders);
    metrics are pipeline proof + gap measurement, not CROHME benchmark numbers.
11. **BTTR fallback NOT executed.** Reason: primary ran reliably (750/750 keys,
    30 real predictions); BTTR needs equal legacy work for a weaker archived model
    with no reason to outperform cross-dataset. Consequence: BTTR stays fallback;
    next accuracy lever = CROHME-style rendering/fine-tune, not model swap.
12. **No phone photos used.** Reason: none available/authorized; task allows
    render-only baseline. Consequence: photo gap unmeasured — needs user-supplied
    authorized photos in a later milestone.

## 2026-10-09T21:35:00+05:30 — Phase 0 foundation choices

1. **Backend venv at `backend/.venv` (Python 3.11.9), pinned `requirements.txt`.**
   Alternatives: root `.venv`, conda, `uv`. Reason: isolates backend deps; matches
   `requires-python >=3.11,<3.13`; reproducible. Consequence: `ml/` will need its own
   env later (PyTorch/CUDA). Unresolved: `uv` vs pip for ML env.

2. **Expo SDK 57 blank-TypeScript scaffold (`eigen-mobile`), Expo Router deferred.**
   Alternatives: tabs template with router now. Reason: Phase 0 asks for minimal coherent
   scaffold; router + screens belong to Phase 1 milestone. Consequence: `mobile/app/`
   dir from the ideal layout does not exist yet. Unresolved: router vs plain stack choice
   in Phase 1.

3. **Discarded template files (`mobile-tmp` AGENTS.md, LICENSE, .gitignore, .claude).**
   Reason: root `AGENTS.md`/`.gitignore` govern; template license text would misstate
   project licensing. Consequence: project currently has no LICENSE file — add one
   (e.g. MIT/Apache-2.0 for own code) in Phase 1 after deciding.

4. **No PyTorch / checkpoint / dataset downloads in Phase 0.**
   Alternatives: install torch now. Reason: task explicitly forbids large downloads before
   model research concludes; RTX 4050 CUDA/cuDNN pins depend on the chosen checkpoint's
   stack. Consequence: no inference claim can be made yet.

5. **Initial model recommendation: PosFormer; fallback: BTTR (MIT code).**
   Alternatives considered: CoMER (reproducible but unlicensed), TAMER (newest but
   smallest community + missing fusion ckpt), pix2tex (wrong domain + NC weights).
   Reason: PosFormer weights in-git, maintained, handles nested structures; BTTR is the
   only permissive-code fallback. Consequence: commercial-use question still open —
   all weights/datasets found are NC or unclear. See `RESEARCH.md`.

6. **Data strategy (proposed): MathWriting-train + CROHME-eval, render strokes→images.**
   Alternatives: CROHME-only, synthetic-only. Reason: 230k MathWriting inks dwarf 9k
   CROHME-train; CROHME tests are the standard benchmark. Consequence: phone-photo gap
   remains — augmentation + small in-domain photo set required later.

7. **Java 8 on PATH rejected for builds; Android SDK absent.**
   Reason: verified `java 1.8.0_401`; current AGP/Gradle need JDK 17+. `ANDROID_HOME`
   empty because Studio still downloading. Consequence: Phase 1 must configure
   Studio-bundled JDK + SDK before any `npm run android` device test.
