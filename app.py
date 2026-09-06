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
        if len(password) < 6:
            return json_error("Password must be at least 6 characters.")
        auth.sign_up(email, password)
        return json_ok({"message": "Account created"})
    except ValueError as error:
        return json_error(str(error))
    except Exception as error:
        return json_error(str(error), 500)


@app.post("/api/login")
def api_login():
    try:
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip()
        password = payload.get("password") or ""
        if not email or not password:
            return json_error("Please enter something first.")
        account = auth.sign_in(email, password)
        session["session_id"] = store.create_session(
            account["email"], account["access_token"]
        )
        return json_ok({"email": account["email"]})
    except ValueError as error:
        return json_error(str(error))
    except Exception as error:
        return json_error(str(error), 500)


@app.post("/api/logout")
def api_logout():
    try:
        session_id, active = current_session()
        if active:
            auth.sign_out(active["access_token"])
            store.wipe_session(session_id)
        session.clear()
        return json_ok({"message": "Session wiped"})
    except Exception as error:
        return json_error(str(error), 500)


if __name__ == "__main__":
    app.run(debug=True)
