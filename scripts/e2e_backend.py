import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import uvicorn

from backend.config import ROOT, Settings
from backend.main import create_app

if __name__ == "__main__":
    (ROOT / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="e2e-", dir=ROOT / ".tmp") as temporary:
        settings = Settings(database_url=f"sqlite:///{Path(temporary) / 'e2e.db'}")
        if os.environ.get("MARSENSE_E2E_AUTH") == "1":
            from backend.auth import password_hash

            user_file = Path(temporary) / "test-users.json"
            user_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "test-reviewer",
                            "username": "reviewer",
                            "name": "Test Reviewer",
                            "role": "MISSION_CONTROL",
                            "password_hash": password_hash("isolated-test-only-password"),
                        }
                    ]
                )
            )
            settings.auth_users_file = str(user_file)
            settings.auth_required = True
            settings.cors_origins = ["http://127.0.0.1:3002"]
            uvicorn.run(create_app(settings), host="127.0.0.1", port=8002)
            sys.exit(0)
        uvicorn.run(create_app(settings), host="127.0.0.1", port=8001)
