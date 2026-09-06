from flask import Flask, session

import config
from services import store

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def current_session():
    """The cookie holds only the session id, all study data stays in RAM."""
    session_id = session.get("session_id")
    if not session_id:
        return None, None
    return session_id, store.get_session(session_id)


if __name__ == "__main__":
    app.run(debug=True)
