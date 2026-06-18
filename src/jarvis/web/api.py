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
