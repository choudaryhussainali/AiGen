"""In RAM session store. Nothing here is ever written to disk."""

import secrets
from datetime import datetime, timezone

_sessions = {}


def _new_session_id():
    return secrets.token_urlsafe(24)


def create_session(email, access_token):
    session_id = _new_session_id()
    now = datetime.now(timezone.utc)
    _sessions[session_id] = {
        "email": email,
        "access_token": access_token,
        "chunks": [],
        "embeddings": None,
        "filename": None,
        "created_at": now,
        "last_seen": now,
    }
    return session_id
