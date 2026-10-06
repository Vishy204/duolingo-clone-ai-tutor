"""Per-IP limits must not be bypassable, and voice has its own daily cap."""
from types import SimpleNamespace

from starlette.requests import Request

from app.core.rate_limit import client_ip
from app.voice import routes as voice


def _req(xff: str | None, peer: str = "10.0.0.1") -> Request:
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


def test_client_ip_ignores_spoofed_forwarded_for():
    # The proxy appends the address it saw; whatever the client put first is attacker-controlled.
    assert client_ip(_req("6.6.6.6, 203.0.113.9")) == "203.0.113.9"
    assert client_ip(_req("203.0.113.9")) == "203.0.113.9"
    assert client_ip(_req(None, peer="127.0.0.1")) == "127.0.0.1"


def test_voice_daily_cap_is_per_ip(db, monkeypatch):
    cfg = SimpleNamespace(daily_sessions=25, ip_daily_sessions=25)
    monkeypatch.setattr(voice, "_ip_sessions", {})
    monkeypatch.setattr(voice, "_sessions_today", lambda db, uid: 0)
    ip = "198.51.100.7"
    assert voice._left(cfg, db, 1, ip) == 25
    for _ in range(25):
        voice._count_ip(ip)
    assert voice._left(cfg, db, 1, ip) == 0          # a brand-new guest on the same IP is still capped
    assert voice._left(cfg, db, 2, "198.51.100.8") == 25
