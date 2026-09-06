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
