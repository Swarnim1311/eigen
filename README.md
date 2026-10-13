# Eigen — Handwritten Mathematics Recognition

Cross-platform app: photograph handwritten math, get recognized LaTeX/symbols, compute results safely.

## Stack

- **Mobile:** React Native + Expo (TypeScript) + Expo Router. Android via Android Studio/emulator or physical device; iOS via physical iPhone + EAS cloud builds.
- **Backend:** Python 3.11 + FastAPI + Pydantic.
- **ML:** PyTorch + PosFormer HMER checkpoint (experimental baseline: 0/30 exact,
  CER 0.912 — see `ml/reports/inference_baseline.md`). SymPy behind a restricted parser.
- **Persistence:** SQLite (local).
- **Tests:** Pytest (backend), Jest/mobile tests later.

## Repo layout

```text
eigen/
  mobile/            # Expo app: 6-screen MVP (Home/Capture/Recognize/Review/Result/History).
                     # Code-verified only as of 2026-10-13 — never run on a device/emulator.
  backend/           # FastAPI app (health + /api/v1 math & recognition)
  ml/                # scripts/, evaluation/, experiments/, reports/
  docs/
    project_context/ # authoritative state: PROJECT_STATE, ARCHITECTURE, DECISIONS, ROADMAP, RESEARCH, CHANGELOG
    architecture/
    decisions/
```

## Quick start (Phase 3 — mobile MVP present, device testing still pending)

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# health: http://127.0.0.1:8000/health
# math:   POST http://127.0.0.1:8000/api/v1/math/evaluate  {"expression": "2*(3+4)^2"}
# recognize (experimental model): POST http://127.0.0.1:8000/api/v1/recognize  (multipart image)
# readiness: http://127.0.0.1:8000/api/v1/ready
python -m pytest -q
# slow real-model integration (loads 78MB ckpt, ~1 min):
$env:EIGEN_TEST_WORKER = "1"; python -m pytest -q -k real_worker
```

The recognizer worker needs `ml/.venv` + `ml/checkpoints/posformer-best.ckpt`
(see `ml/requirements.txt` and `docs/project_context/RESEARCH.md`); without them
`/recognize` honestly reports 503 `model_unavailable`.

### Mobile

```powershell
cd mobile
npm install
npx expo start
# Android: press `a` (emulator/device); iOS: physical iPhone via Expo Go/dev build
```

#### Configuring the development API URL (required on physical devices)

The app reads the backend address from `EXPO_PUBLIC_API_URL` (see
`mobile/.env.example`). A phone cannot reach the Windows host via
`localhost`, so set the host's LAN address before starting Expo:

```powershell
# 1. Find the host LAN address, e.g. 192.168.1.10
ipconfig  # look under "Wireless LAN adapter Wi-Fi" → IPv4 Address
# 2. Start the backend on all interfaces
cd backend; .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
# 3. Point the app at it (dev only — never ship an HTTP/LAN URL to production)
$env:EXPO_PUBLIC_API_URL = "http://192.168.1.10:8000"
cd ..\mobile; npx expo start
```

Fallbacks when the variable is unset: the Expo host address in dev, else
`http://10.0.2.2:8000` (Android-emulator alias for host localhost).
`EXPO_PUBLIC_*` values are baked into the JS bundle — never put production
secrets in them.

See `docs/project_context/` for current state, decisions, roadmap, and research.
`AGENTS.md` holds persistent working rules.
