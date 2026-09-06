"""In RAM session store. Nothing here is ever written to disk."""

import secrets

_sessions = {}


def _new_session_id():
    return secrets.token_urlsafe(24)
