import hashlib
import hmac
import os
from typing import Optional


def get_app_secret() -> bytes:
    secret = (
        os.environ.get("PSEUDO_ID_SECRET") or os.environ.get("JWT_SECRET_KEY") or "fallback-secret"
    )
    return secret.encode("utf-8")


def compute_user_pseudo_id(user_id: Optional[str | int]) -> str:
    if user_id is None:
        return "anonymous"
    msg = str(user_id).encode("utf-8")
    digest = hmac.new(get_app_secret(), msg, hashlib.sha256).hexdigest()
    # Keep it short for logs
    return digest[:16]
