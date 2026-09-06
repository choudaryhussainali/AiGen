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


def wipe_session(session_id):
    # Python cannot guarantee that freed memory is overwritten, so this is not
    # a secure erase. What it does guarantee is that no study content was ever
    # written to persistent storage and that every reference to it is dropped
    # here, making it eligible for garbage collection.
    _sessions.pop(session_id, None)
