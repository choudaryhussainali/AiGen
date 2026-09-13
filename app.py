import io
import json

from flask import Flask, Response, jsonify, redirect, render_template, request, session
from werkzeug.exceptions import RequestEntityTooLarge

import config
from services import ai, auth, documents, store, youtube

app = Flask(__name__)
app.secret_key = config.FLASK_SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Two megabytes of headroom over the file cap, so the friendly size message in
# read_upload fires first and only far larger bodies are refused outright.
app.config["MAX_CONTENT_LENGTH"] = (config.MAX_FILE_MB + 2) * 1024 * 1024


def json_ok(data):
    return jsonify({"ok": True, "data": data})


def json_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


TOO_LARGE = f"File is too large. Maximum size is {config.MAX_FILE_MB} MB."


def get_upload():
    """Touching request.files raises 413 once the body passes the size cap."""
    try:
        return request.files.get("file")
    except RequestEntityTooLarge:
        raise ValueError(TOO_LARGE)


def read_upload(upload, extensions, format_message):
    """Reads an upload into memory, nothing is ever written to disk."""
    if not upload.filename.lower().endswith(extensions):
        raise ValueError(format_message)
    data = upload.read()
    if len(data) > config.MAX_FILE_MB * 1024 * 1024:
        raise ValueError(TOO_LARGE)
    return data


def current_session():
    """The cookie holds only the session id, all study data stays in RAM."""
    session_id = session.get("session_id")
    if not session_id:
        return None, None
    return session_id, store.get_session(session_id)


def signed_out_page(template):
    """Visitor pages, anyone already logged in goes straight to the dashboard."""
    _, active = current_session()
    return redirect("/dashboard") if active else render_template(template)


@app.get("/")
def index():
    return signed_out_page("landing.html")


@app.get("/login")
def login_page():
    return signed_out_page("auth.html")


@app.get("/dashboard")
def dashboard():
    _, active = current_session()
    if active is None:
        return redirect("/")
    return render_template(
        "dashboard.html", email=active["email"], languages=config.SUMMARY_LANGUAGES
    )


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
        first_name = (payload.get("first_name") or "").strip()[:50]
        last_name = (payload.get("last_name") or "").strip()[:50]
        if not first_name or not last_name:
            return json_error("Please enter your first name and last name.")
        auth.sign_up(email, password, first_name, last_name)
        return json_ok({"message": "Account created"})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


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
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/notes/upload")
def api_notes_upload():
    try:
        session_id, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        upload = get_upload()
        if upload is None:
            return json_error("Please choose a file first.")
        data = read_upload(upload, (".pdf",), "Please upload a PDF file.")
        pages = documents.extract_pdf_pages(io.BytesIO(data))
        chunks = documents.chunk_pages(pages)
        embeddings = ai.embed_documents([chunk["text"] for chunk in chunks])
        full_text = "\n".join(page["text"] for page in pages)
        summary = ai.summarize_notes(full_text[:config.MAX_SUMMARY_CHARS])
        store.set_document(session_id, chunks, embeddings, upload.filename, summary)
        return json_ok(
            {"summary": summary, "filename": upload.filename, "pages": len(pages)}
        )
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


def answer_events(session_id, question, pieces, shown):
    """Streams the answer text, then a NUL byte and a JSON trailer with the tidy answer."""
    answer = ""
    try:
        for piece in pieces:
            answer += piece
            yield piece
    except Exception:
        app.logger.exception("answer stream interrupted")
        yield "\0" + json.dumps({"error": "The answer was cut off. Please ask again."})
        return
    final = documents.plain_markdown(answer).strip()
    if not final:
        yield "\0" + json.dumps({"error": "The model returned an empty response. Please try again."})
        return
    store.add_turn(session_id, question, final)
    yield "\0" + json.dumps({"answer": final, "pages": documents.cited_pages(final, shown)})


@app.post("/api/notes/ask")
def api_notes_ask():
    try:
        session_id, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        question = (request.get_json(silent=True) or {}).get("question", "").strip()
        if not question:
            return json_error("Please enter something first.")
        if not active["chunks"]:
            return json_error("Upload a PDF before asking questions.")
        pieces, shown = ai.stream_from_notes(
            question, active["chunks"], active["embeddings"],
            active["summary"], active["history"],
        )
        events = answer_events(session_id, question, pieces, shown)
        return Response(events, mimetype="text/plain")
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/exam")
def api_exam():
    try:
        _, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        outline = (request.get_json(silent=True) or {}).get("outline", "").strip()
        if not outline:
            return json_error("Please enter something first.")
        return json_ok({"plan": ai.build_exam_plan(outline)})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/paper/solve")
def api_paper_solve():
    try:
        _, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        upload = get_upload()
        if upload is None:
            return json_error("Please choose a file first.")
        message = "Please upload a JPG or PNG image."
        data = read_upload(upload, (".jpg", ".jpeg", ".png"), message)
        if len(data) > 3 * 1024 * 1024:
            raise ValueError("That image is too large. Please upload one under 3 MB.")
        is_png = upload.filename.lower().endswith(".png")
        mime_type = "image/png" if is_png else "image/jpeg"
        return json_ok({"solution": ai.solve_paper(data, mime_type)})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/video")
def api_video():
    try:
        _, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        payload = request.get_json(silent=True) or {}
        url = (payload.get("url") or "").strip()
        language = payload.get("language") or "English"
        if not url:
            return json_error("Please enter something first.")
        if language not in config.SUMMARY_LANGUAGES:
            return json_error("Please choose a summary language from the list.")
        video_id = youtube.extract_video_id(url)
        parts, complete = youtube.split_transcript(youtube.fetch_transcript(video_id))
        summary = ai.summarize_video(ai.condense_transcript(parts), language)
        if not complete:
            summary += "\n\nThis video is very long, so only its first part was summarised."
        return json_ok({"summary": summary, "video_id": video_id})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/topic")
def api_topic():
    try:
        _, active = current_session()
        if active is None:
            return json_error("Not authenticated", 401)
        topic = (request.get_json(silent=True) or {}).get("topic", "").strip()
        if not topic:
            return json_error("Please enter something first.")
        return json_ok({"explanation": ai.explain_topic(topic)})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


@app.post("/api/logout")
def api_logout():
    try:
        session_id, active = current_session()
        if active:
            auth.sign_out()
            store.wipe_session(session_id)
        session.clear()
        return json_ok({"message": "Session wiped"})
    except ValueError as error:
        return json_error(str(error))
    except Exception:
        app.logger.exception("unhandled error")
        return json_error("Something went wrong. Please try again.", 500)


if __name__ == "__main__":
    app.run(debug=True)
