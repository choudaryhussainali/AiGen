# AiGen: Project Rules

Full spec lives in AiGen_Master_Prompt.md. Read it if anything here is unclear.

## Hard rules
- Vanilla HTML, CSS and JavaScript only. No React, no Tailwind, no build step, no npm.
- No LangChain, no ChromaDB, no Celery, no Redis, no Docker, no ORM.
- Plain module-level functions. One class permitted in the entire project.
- Synchronous Flask only. No async, no threads, no background workers.
- Every function under 40 lines. Every file under 300 lines.
- Exactly 12 source files. The structure is fixed in spec section 5.
- No dead code, no placeholders, no unused imports, no unused CSS.
- No emojis anywhere.
- No em dashes and no en dashes anywhere, including commit messages.
  Never emit the characters U+2014 or U+2013.
- Do not add features beyond spec section 6.

## Commit rules
- Conventional Commits: type(scope): subject
- Types: feat, fix, refactor, style, docs, chore, build, perf
- Imperative mood, lowercase, no full stop, under 60 characters
- One small complete change per commit. If the subject needs the word
  "and", the commit is too big and must be split.
- Target is 200 commits minimum across the project.
- Never commit .env, .claude/ or AiGen_Master_Prompt.md. Stage specific
  files, never use git add .
- Never backdate commits or rewrite history.

## Working style
- Work through the phases in spec section 15.5 in order, continuously.
- Commit continuously while building, never in a batch at the end.
- Push at the end of every phase.
- Run the section 15.8 self check at the end of every phase and fix what
  it flags before starting the next phase.
- Do not stop to ask whether to continue. Only stop for a real blocker:
  a missing key, a failing install, or an unresolvable spec ambiguity.
- After any context compaction, re-read this file before continuing.
