# Local launcher and reproducible setup

From D:\MARSENSE, after installing Python 3.12 and Node 24:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install -r ai/requirements-lock.txt --index-url https://download.pytorch.org/whl/cpu
cd frontend
npm ci
cd ..
powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

`backend/requirements-lock.txt` records the verified Windows environment; CPU
PyTorch uses its separate official index. Compatible dependency ranges for other
environments remain in the normal requirement files. npm ci uses its package lock.

Open http://127.0.0.1:3000/mission. Services run on loopback, with logs and process
records under data/runtime. Stop with scripts/stop-local.ps1. Evidence remains
in SQLite. The launcher refuses to replace occupied ports.

For production frontend validation, run npm run build, then npm run start from
frontend while the local API runs. Docker Compose is an alternative that binds
host ports to loopback and preserves runtime data in a named volume; Docker is
unavailable on this workstation, so container startup has not been verified.

The backend bearer API mode is separate from the local browser UI. Identity-bound
reviewers, session handling and authenticated proxying remain production requirements.
