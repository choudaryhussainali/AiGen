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
| Transcripts | youtube-transcript-api |
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
