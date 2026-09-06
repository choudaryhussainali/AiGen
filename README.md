# AiGen: AI Powered Smart Learning Assistant

AiGen is a web app that puts five AI study tools behind one login. It is built
with Flask, vanilla HTML, CSS and JavaScript, and Google Gemini. Every piece of
study content a user uploads lives in server RAM only and is destroyed the
moment they log out.

## The five tools

- **Notes Summarizer** uploads a PDF, summarises it, then answers follow up
  questions about it with page citations.
- **Exam Prep** turns a pasted course outline into a topic by topic study plan.
- **Past Paper Solver** reads a question image and solves it with working shown.
- **Video Summarizer** turns a YouTube link into a topic wise summary.
- **Topic Explainer** explains any topic with a definition, an analogy and three
  key points.

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 or newer |
| Web framework | Flask 3, synchronous |
| Templating | Jinja2 |
| Frontend | HTML5, CSS3, vanilla JavaScript, no build step |
| Auth | Supabase Python client, email and password |
| LLM | Google Gemini via google-genai, text and vision |
| Embeddings | Gemini embedding model |
| Vector search | numpy cosine similarity over a list in RAM |
| PDF text | pypdf |
| Transcripts | youtube-transcript-api 1.2.4 or newer |
| Sessions | Python dictionary in RAM |

## Setup

```bash
git clone https://github.com/choudaryhussainali/AiGen.git
cd AiGen
python -m venv venv
venv\Scripts\activate        # on macOS or Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env       # on macOS or Linux: cp .env.example .env
python app.py
```

Fill the four values in `.env` before starting the server, then open
http://127.0.0.1:5000 in a browser.

## Where the keys come from

| Variable | Where to get it |
|---|---|
| `FLASK_SECRET_KEY` | Any random string you invent |
| `SUPABASE_URL` | Supabase dashboard, Project Settings, API |
| `SUPABASE_KEY` | Same page, the **anon public** key, never `service_role` |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey |

The Supabase key used on the server is the anon public key, which is safe to use
from application code because row level security governs what it can reach.

In the Supabase dashboard under Authentication, Providers, Email, turn
"Confirm email" off if you want new accounts to be able to log in straight away.
Leaving it on means a new user has to click the link in their inbox first.

## How Zero Persistence works

Logging in creates an entry in a plain Python dictionary in `services/store.py`,
holding the user's email, their Supabase access token, and, once they upload a
PDF, its text chunks and embeddings. Nothing study related is ever written to
disk or to the database, uploads are read from the request stream straight into
memory, and the browser cookie carries only the session id. Logging out deletes
the whole entry, and any session untouched for 60 minutes is deleted on the next
request. Python cannot guarantee that freed memory is overwritten, so this is not
a secure erase, but the content never reaches persistent storage and every
reference to it is dropped.

## Privacy scope

> Zero-Persistence applies to AiGen's own infrastructure: uploaded content lives
> in server RAM only, is never written to disk or to the database, and is
> destroyed on logout. Content sent to the Google Gemini API for inference is
> governed by Google's API terms, which are outside AiGen's control.

## Design deviation from proposal

The original proposal named EasyOCR and Tesseract for reading past paper images.
Neither is used here, because EasyOCR pulls in roughly 2 GB of PyTorch, needs
model downloads, is slow on CPU, and still cannot read mathematical notation.
Gemini vision reads the image directly, handles handwriting and formulas, and
lets one API call both read the question and solve it, which removes an entire
dependency and an entire processing stage.

## Known limitations

- English only. The prompts and the transcript lookup both assume English.
- No chat history. Follow up answers are not remembered between questions.
- One worker only. Sessions live in the memory of a single process, so production
  needs a single Gunicorn worker (`gunicorn -w 1 app:app`). A second worker would
  not see the first one's sessions.
- Uploads are capped at 10 MB, for both PDFs and images.
- Videos without subtitles cannot be summarised, because there is no transcript
  to read.
- On the Gemini free tier the embedding endpoint allows 100 requests a minute,
  so a very large PDF can hit that limit and ask you to retry.
