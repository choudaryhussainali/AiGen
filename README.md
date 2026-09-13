# AiGen: AI Powered Smart Learning Assistant

AiGen is a web app that puts five AI study tools behind one login. It is built
with Flask, vanilla HTML, CSS and JavaScript, Groq for text and vision, and an
embedding model that runs on the server itself. Every piece of study content a
user uploads lives in server RAM only and is destroyed the moment they log out.

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
| Frontend | Jinja2, HTML5, CSS3, vanilla JavaScript, no build step |
| Auth | Supabase Python client, email and password |
| LLM | Groq chat completions over plain requests, text and vision |
| Embeddings | fastembed running locally, all-MiniLM-L6-v2 |
| Vector search | numpy cosine similarity over a RAM list |
| PDF text | pypdf |
| Transcripts | youtube-transcript-api 1.2.4 or newer |
| Sessions | Python dictionary in RAM |

## Setup

```bash
git clone https://github.com/choudaryhussainali/AiGen.git
cd AiGen
python -m venv venv
source venv/bin/activate     # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env         # on Windows: copy .env.example .env
python app.py
```

Fill the four values in `.env`, start the server, and open http://127.0.0.1:5000.
The first start downloads the embedding model, about 90 MB, and caches it.

## Where the keys come from

| Variable | Where to get it |
|---|---|
| `FLASK_SECRET_KEY` | Any random string you invent |
| `SUPABASE_URL` | Supabase dashboard, Project Settings, API |
| `SUPABASE_KEY` | Same page, the **anon public** key, never `service_role` |
| `GROQ_API_KEY` | https://console.groq.com/keys, the only AI key the app needs |

The key used on the server is the anon public key, which is safe in application
code because row level security governs what it can reach. In the Supabase
dashboard under Authentication, Providers, Email, turn "Confirm email" off if you
want new accounts to log in straight away, otherwise a new user has to click the
link in their inbox first.

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
> destroyed on logout. Document chunks are embedded on the AiGen server and never
> sent to a third party. Prompts for text generation do go to Groq: note excerpts,
> up to 12,000 characters of a PDF or transcript, and uploaded images. That half
> is governed by Groq's API terms, which are outside AiGen's control.

## Why embeddings run locally

A hosted embedding model made PDF indexing depend on a provider request quota.
The model now runs in the server process through fastembed, so indexing needs no
key, no network after the first download, and has no request limit.

## Design deviation from proposal

The original proposal named EasyOCR and Tesseract for reading past paper images.
Neither is used here, because EasyOCR pulls in roughly 2 GB of PyTorch, needs
model downloads, is slow on CPU, and still cannot read mathematical notation.
A vision model on Groq reads the image directly and lets one API call both read
the question and solve it, which removes an entire dependency and an entire
processing stage.

## Known limitations

- English only, in both the prompts and the transcript lookup.
- No chat history, follow up answers are not remembered between questions.
- One worker only. Sessions live in one process's memory, so production needs a
  single Gunicorn worker (`gunicorn -w 1 app:app`); a second would not see them.
- Uploads are capped at 10 MB, for both PDFs and images.
- Videos without subtitles cannot be summarised, there is no transcript to read.
- The Gemini free tier is small. It allows 20 `gemini-2.5-flash` requests a day
  and 100 embedding requests a minute, so a day of testing can use it up. Enable
  billing on the Google Cloud project behind the key to lift both.
