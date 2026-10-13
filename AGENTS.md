# AGENTS.md — Eigen persistent working rules

## 1. Context-first workflow (mandatory)

- Before any change: read `docs/project_context/PROJECT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, and `RESEARCH.md` (plus `CHANGELOG.md` for recent session notes).
- After any change: update every affected context file with an ISO 8601 local-timestamp entry. Never invent timestamps; use actual execution time.
- `docs/project_context/` is the source of truth. Code and docs must agree; if they diverge, fix docs in the same session.
- Preserve valid existing work. Inspect the repo before scaffolding; never overwrite unrelated files.

## 2. Architecture

- Mobile: React Native + Expo + TypeScript + Expo Router. Shared logic must stay platform-agnostic (Android + iOS non-negotiable).
- Backend: Python 3.11 + FastAPI + Pydantic. All math evaluation goes through a restricted parser → SymPy; never `eval()`/`sympify()` raw client input.
- ML: PyTorch + one verified pretrained HMER checkpoint. Prefer reproducible inference before any fine-tuning. Never train from scratch; never ship mocked predictions as real.
- Comms: mobile ↔ backend over HTTPS (JSON). No Android-only deps in shared logic.
- Persistence: SQLite local only in early phases.

## 3. Windows compatibility

- Dev machine: Windows 11, Python 3.11.9, Node 24.x, Git 2.53, RTX 4050 6 GB / 16 GB RAM. Do not reinstall toolchains without a demonstrated incompatibility.
- PowerShell 5.1 is the shell. Use `; if ($?) { ... }` for dependent commands (no `&&`). Quote paths with spaces. Use `workdir` instead of `cd`.
- Java 8 (1.8.0_401) was found on PATH on 2026-10-09 and is NOT suitable for current Android Studio/Gradle — use the JDK bundled with Android Studio (JDK 17+) instead. Never downgrade `JAVA_HOME` to Java 8 for builds.
- Android SDK path not yet present (Studio still downloading as of Phase 0). Do not assume `ANDROID_HOME` exists; report missing prerequisites with the smallest manual step.
- iOS Simulator does not run on Windows. iOS testing = physical iPhone + EAS cloud builds.

## 4. Scope control

- Implement only the requested milestone. Do not build full screens, full recognition API, training loops, dataset/checkpoint downloads, deployments, or prod signing unless explicitly asked.
- Keep scaffolds minimal: no empty boilerplate, no unnecessary abstractions, no extra deps to "look complete".
- Never commit: venvs, `node_modules/`, datasets, checkpoints (`*.pt/*.pth/*.bin/*.onnx/*.ckpt/*.safetensors`), `.env`/secrets, uploads, caches. See `.gitignore`.
- Distinguish implemented vs proposed vs verified in every report. Do not claim device compatibility, model accuracy, or license suitability without evidence.

## 5. Code quality & testing

- Backend: type with Pydantic, format with `ruff` (or black), lint, `pytest -q` must pass before finishing a backend task.
- Mobile: TypeScript strict, ESLint/Prettier per Expo defaults, `npx tsc --noEmit` clean when TS files exist.
- Reproducible manifests only: `backend/requirements.txt` (+ lock where practical), `mobile/package.json` + `package-lock.json`. No global installs when project-local applies.
- If a scaffold/install/test fails, diagnose the real error; do not continue on a broken project or silently skip.

## 6. Research honesty

- Primary sources required (repo + docs + paper + license file). Record URL + access date for every claim.
- Never equate "repo exists" with "checkpoint available and legally usable". Verify weights URL, weight license, code license, and dataset licenses separately.
- Label every statement: Verified / Estimate / Unverified. No fabricated benchmarks, licenses, or download links.

## 7. Session close-out

- Run applicable checks (`pytest`, `tsc`, `expo --version`), record exact versions, commands, and outcomes in `CHANGELOG.md`.
- Update `PROJECT_STATE.md` (state/blockers), `ROADMAP.md` (milestone status), `RESEARCH.md` (if investigated), `DECISIONS.md` (if decided).
