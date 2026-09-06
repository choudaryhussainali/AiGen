from flask import Flask, jsonify, request, session

import config
from services import auth, store

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


def json_ok(data):
    return jsonify({"ok": True, "data": data})


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def current_session():
    """The cookie holds only the session id, all study data stays in RAM."""
    session_id = session.get("session_id")
    if not session_id:
        return None, None
    return session_id, store.get_session(session_id)


@app.post("/api/signup")
def api_signup():
    try:
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()
        password = payload.get("password") or ""
        if not email or not password:
            return json_error("Please enter something first.")
        auth.sign_up(email, password)
        return json_ok({"message": "Account created"})
    except ValueError as error:
        return json_error(str(error))
    except Exception as error:
        return json_error(str(error), 500)


if __name__ == "__main__":
    app.run(debug=True)
