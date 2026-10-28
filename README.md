# 29 · notesapp

Server-rendered notes with FastAPI + HTMX, no build step.

## Run

```bash
uvicorn notesapp.app:create_app --factory
```

## Test

```bash
pytest projects/29-notes-app -q
```

## What it demonstrates

- HTML-first: every route returns HTML, HTMX upgrades the interaction
- Server-side rendering means the app works without JavaScript
- Jinja2 auto-escaping verified by a test that posts `<script>`
- SQLite with parameterised queries throughout
