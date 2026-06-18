# Jarvis Web UI — Design Spec

**Date:** 2026-06-18  
**Status:** Approved  
**Scope:** First web UI for Jarvis — local network only, simple but polished dark theme.

---

## 1. Goal

Give the user a browser-based way to interact with Jarvis from any device on the LAN (laptop, phone), without needing SSH. Complements the voice interface — same brain, same memory store, different surface.

---

## 2. Layout

Two screens navigated via React Router:

### Home (`/`)
- **Header:** "JARVIS" logotype (top left) + Ollama status pill (top right, green/red)
- **Status cards (3):** Model name, active projects count, last response latency
- **Jarvis orb:** Central glowing purple orb — the primary call to action
  - Two buttons below: "🎤 Falar" (reserved for Phase 3 voice) and "✏️ Escrever" → navigates to `/chat`
  - Clicking the orb directly also navigates to `/chat`

### Chat (`/chat`)
- **Left sidebar (~30% width):**
  - "JARVIS" logotype + "← Início" back link at bottom
  - Project list — each entry shows name + status badge
  - Clicking a project **selects it as active context** (purple highlight) — deselect by clicking again
  - Active context is automatically injected into the next message sent
- **Main area:**
  - Message thread (user bubbles right-aligned, Jarvis bubbles left-aligned)
  - Tokens stream in as they arrive (SSE)
  - Input bar at bottom: text field + mic icon (voice placeholder) + send button

---

## 3. Architecture

```
Browser (laptop / phone)
  React + Vite + Tailwind
  web/dist/ (static, built on laptop)
        ↕ REST + SSE  :7777
Raspberry Pi 5 (always-on)
  FastAPI — src/jarvis/web/api.py
    ├── serves web/dist/ as static files
    ├── Brain (brain.py) — reused as-is
    └── Store (store.py) — reused as-is
        ↕ HTTP  :11434
Laptop (on-demand)
  Ollama + qwen3:4b · RTX 3060
```

**Build workflow:** Edit frontend on laptop → `npm run build` → commit `web/dist/` → Pi runs `git pull`. No Node.js on the Pi.

**Port:** `7777` (configurable via `config.yaml` as `web.port`).

---

## 4. API Endpoints

All endpoints under `/api/`. FastAPI serves `web/dist/index.html` for any unmatched route (SPA fallback).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/status` | `{ollama_ok, model, projects_count, last_latency_ms}` — latency tracked by Brain on each `chat()` call |
| `GET` | `/api/projects` | Array of all Project objects |
| `POST` | `/api/projects` | Create project `{name, goal, status}` |
| `PATCH` | `/api/projects/{name}` | Update any project fields |
| `DELETE` | `/api/projects/{name}` | Delete a project |
| `POST` | `/api/chat` | Send message, returns SSE token stream |
| `DELETE` | `/api/chat/history` | Reset conversation history |

### Chat SSE format
```
POST /api/chat
Body: { "message": "string", "context_project": "string | null" }

Stream events:
  data: {"token": "Olá"}
  data: {"token": "!"}
  data: {"done": true, "latency_ms": 1240}
```

---

## 5. Frontend Components

```
web/src/
├── pages/
│   ├── Home.tsx          — status cards + orb
│   └── Chat.tsx          — sidebar + message thread
├── components/
│   ├── Orb.tsx           — glowing orb with CSS pulse animation
│   ├── StatusCard.tsx    — individual status card (model / projects / latency)
│   ├── ProjectSidebar.tsx — project list, active-context selection
│   ├── Message.tsx       — chat bubble (user | jarvis variants)
│   └── ChatInput.tsx     — text input + send + mic placeholder
├── hooks/
│   ├── useChat.ts        — SSE streaming → token accumulation → message list
│   └── useProjects.ts    — fetch projects list (read-only in v1)
└── lib/
    └── api.ts            — base URL constant + typed fetch helpers
```

**State management:** `useState` / `useEffect` only — no Redux. Active context project stored in `Chat.tsx` local state and passed down.

**Routing:** React Router v6, two routes: `/` and `/chat`.

---

## 6. Styling

- **Theme:** Dark, Tailwind — background `#0a0c14`, surface `#111827`, accent `#6366f1` (indigo)
- **Orb:** Radial gradient (indigo → deep purple) + `box-shadow` glow + CSS keyframe pulse
- **Status pill:** Green (`#22c55e`) when Ollama reachable, red when not
- **Active context project:** Indigo left border + subtle indigo background in sidebar

---

## 7. Config changes

Add to `config/config.example.yaml`:
```yaml
web:
  port: 7777
```

`api.py` reads this at startup. `config.yaml` is already gitignored.

---

## 8. New dependencies

**Python (Pi):**
- `fastapi`
- `uvicorn[standard]`
- `sse-starlette` (SSE support)

**Node (laptop, dev only):**
- Standard Vite + React + Tailwind scaffold (`npm create vite`)
- `react-router-dom`

---

## 9. File layout additions

```
jarvis/
├── web/                      ← new
│   ├── src/                  ← frontend source (not served)
│   ├── dist/                 ← built output (committed, served by FastAPI)
│   ├── package.json
│   └── vite.config.ts
└── src/jarvis/
    └── web/
        └── api.py            ← new FastAPI app
```

---

## 10. Out of scope (for now)

- Authentication / access control
- Tailscale / remote access
- Voice input in the browser (reserved for Phase 3 voice loop)
- Conversation history persistence across server restarts
- Project creation/editing in the browser — the API has POST/PATCH/DELETE endpoints but the v1 UI only reads projects; manage them via the CLI for now
