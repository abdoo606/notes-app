"""HTML-first app: every route returns HTML, HTMX upgrades it without a build step."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

TEMPLATES = Path(__file__).parent.parent / "templates"

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    done INTEGER NOT NULL DEFAULT 0
);
"""


def create_app(db_path: str = ":memory:") -> FastAPI:
    app = FastAPI(title="notesapp")
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    connection.commit()
    app.state.db = connection

    def templates(request: Request) -> Jinja2Templates:
        return Jinja2Templates(directory=str(TEMPLATES))

    def all_notes() -> list[dict]:
        rows = app.state.db.execute("SELECT * FROM notes ORDER BY done, id DESC").fetchall()
        return [dict(row) for row in rows]

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        notes = all_notes()
        context = {"request": request, "notes": notes, "remaining": sum(not n["done"] for n in notes)}
        return templates(request).TemplateResponse(request, "index.html", context)

    @app.post("/notes", response_class=HTMLResponse)
    def add_note(request: Request, title: str = Form(...), body: str = Form(default="")) -> HTMLResponse:
        title = title.strip()
        if not title:
            raise HTTPException(status_code=422, detail="title must not be blank")
        app.state.db.execute("INSERT INTO notes (title, body) VALUES (?, ?)", (title, body.strip()))
        app.state.db.commit()
        return index(request)

    @app.post("/notes/{note_id}/toggle", response_class=HTMLResponse)
    def toggle(request: Request, note_id: int) -> HTMLResponse:
        row = app.state.db.execute("SELECT done FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="note not found")
        app.state.db.execute("UPDATE notes SET done = ? WHERE id = ?", (0 if row["done"] else 1, note_id))
        app.state.db.commit()
        return index(request)

    @app.delete("/notes/{note_id}", response_class=HTMLResponse)
    def delete(request: Request, note_id: int) -> HTMLResponse:
        cursor = app.state.db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        app.state.db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="note not found")
        return index(request)

    @app.get("/health")
    def health() -> dict[str, str]:
        app.state.db.execute("SELECT 1")
        return {"status": "ok"}

    return app


def serve() -> None:  # pragma: no cover - entry point
    import uvicorn

    uvicorn.run(create_app("notes.db"), host="0.0.0.0", port=8000)


__all__ = ["create_app", "serve", "RedirectResponse"]
