"""Load the JWT signing key from environment or local dev file."""

import os
from pathlib import Path


def get_jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")

    if not secret:
        root = Path(__file__).resolve().parents[2]
        path = root / ".auth_jwt_secret"

        if not path.is_file():
            raise RuntimeError("JWT signing key is not configured")

        secret = path.read_text(encoding="utf-8").strip()

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT signing key must contain 32 bytes")

    return secret
