"""FastAPI web server — serves the React UI and exposes the Jarvis REST/SSE API."""

import asyncio
import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Optional

import requests
import yaml
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from jarvis.brain import Brain
from jarvis.memory.providers import get_provider
from jarvis.memory.store import Store

_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "config.yaml"
_DIST_PATH = Path(__file__).parent.parent.parent.parent / "web" / "dist"
_EXECUTOR = ThreadPoolExecutor(max_workers=1)
_cfg_cache: Optional[dict] = None

app = FastAPI(title="Jarvis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── singletons — lazy init so importing the module is safe without config ──────

_store: Optional[Store] = None
_brain: Optional[Brain] = None


def _load_config() -> dict:
    global _cfg_cache
    if _cfg_cache is None:
        with _CONFIG_PATH.open() as f:
            _cfg_cache = yaml.safe_load(f)
    return _cfg_cache


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store


def get_brain() -> Brain:
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain


# ── models ────────────────────────────────────────────────────────────────────

class ChatBody(BaseModel):
    message: str
    context_project: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    goal: str = ""
    status: str = "idea"


class ProjectUpdate(BaseModel):
    goal: Optional[str] = None
    status: Optional[str] = None
    where_i_left_off: Optional[str] = None
    next_step: Optional[str] = None
    notes: Optional[str] = None


# ── /api/status ───────────────────────────────────────────────────────────────

@app.get("/api/status")
def api_status(store: Store = Depends(get_store), brain: Brain = Depends(get_brain)):
    cfg = _load_config()
    b = cfg["brain"]
    url = f"http://{b['laptop_ip']}:{b['ollama_port']}/api/tags"
    try:
        ok = requests.get(url, timeout=3).ok
    except Exception:
        ok = False
    return {
        "ollama_ok": ok,
        "model": b["model"],
        "projects_count": len(store.list_all()),
        "last_latency_ms": brain.last_latency_ms,
    }


# ── /api/projects ─────────────────────────────────────────────────────────────

@app.get("/api/projects")
def list_projects(store: Store = Depends(get_store)):
    return [asdict(p) for p in store.list_all()]


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectCreate, store: Store = Depends(get_store)):
    try:
        p = store.create(body.name, goal=body.goal, status=body.status)
    except sqlite3.IntegrityError:
        raise HTTPException(409, f"Projeto '{body.name}' já existe.")
    return asdict(p)


@app.patch("/api/projects/{name}")
def update_project(name: str, body: ProjectUpdate, store: Store = Depends(get_store)):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    p = store.update(name, **fields)
    if p is None:
        raise HTTPException(404, f"Projeto '{name}' não encontrado.")
    return asdict(p)


@app.delete("/api/projects/{name}", status_code=204)
def delete_project(name: str, store: Store = Depends(get_store)):
    if not store.delete(name):
        raise HTTPException(404, f"Projeto '{name}' não encontrado.")


# ── /api/chat ─────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(
    body: ChatBody,
    store: Store = Depends(get_store),
    brain: Brain = Depends(get_brain),
):
    context: Optional[str] = None
    if body.context_project:
        provider = get_provider(body.context_project, store)
        if provider:
            context = provider()

    async def _event_gen():
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()

        def _stream():
            try:
                for token in brain.chat(body.message, context=context):
                    loop.call_soon_threadsafe(q.put_nowait, ("token", token))
            except Exception as exc:
                loop.call_soon_threadsafe(q.put_nowait, ("error", str(exc)))
            else:
                loop.call_soon_threadsafe(q.put_nowait, ("done", None))

        _start = time.monotonic()
        asyncio.ensure_future(loop.run_in_executor(_EXECUTOR, _stream))

        while True:
            kind, value = await q.get()
            if kind == "token":
                yield {"data": json.dumps({"token": value})}
            elif kind == "error":
                yield {"data": json.dumps({"error": value})}
                break
            else:
                ms = round((time.monotonic() - _start) * 1000)
                yield {"data": json.dumps({"done": True, "latency_ms": ms})}
                break

    return EventSourceResponse(_event_gen())


@app.delete("/api/chat/history", status_code=204)
def reset_chat(brain: Brain = Depends(get_brain)):
    brain.reset()


# ── SPA fallback (must be last) ───────────────────────────────────────────────

if (_DIST_PATH / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST_PATH / "assets")), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    index = _DIST_PATH / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Frontend não compilado. Corre: cd web && npm run build"}
