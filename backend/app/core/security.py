from datetime import timedelta

import jwt

from app.core.clock import utcnow
from app.core.config import get_settings

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    s = get_settings()
    now = utcnow()
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(days=s.jwt_ttl_days), "typ": "guest"}
    return jwt.encode(payload, s.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
