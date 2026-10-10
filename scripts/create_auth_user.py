"""Provision a prototype user into a private operator-managed file, never source code."""

import argparse
import getpass
import json
from pathlib import Path
from uuid import uuid4

from backend.auth import password_hash


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=["ASTRONAUT", "MISSION_CONTROL", "ADMIN"], required=True)
    args = parser.parse_args()
    password = getpass.getpass("Password (at least 15 characters): ")
    if len(password) < 15 or password != getpass.getpass("Repeat password: "):
        raise ValueError("Passwords must match and contain at least 15 characters")
    users = json.loads(args.file.read_text()) if args.file.exists() else []
    if any(u["username"] == args.username for u in users):
        raise ValueError("Username already exists; refusing overwrite")
    users.append(
        {
            "id": str(uuid4()),
            "username": args.username,
            "name": args.name,
            "role": args.role,
            "password_hash": password_hash(password),
        }
    )
    args.file.parent.mkdir(parents=True, exist_ok=True)
    args.file.write_text(json.dumps(users, indent=2))
    args.file.chmod(0o600)
    print("User provisioned. Restrict the file ACL to the server account and restart the API.")


if __name__ == "__main__":
    main()
