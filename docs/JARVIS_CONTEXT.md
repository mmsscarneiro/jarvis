# Project Jarvis — Context Document for Claude Code

> Hand this file to Claude Code as the starting context. It explains the full
> line of thinking, the constraints, the hardware, the architecture, and the
> phased build plan. Read it top to bottom before suggesting code.

---

## 1. The vision (what I'm actually trying to build)

A personal, voice-activated AI assistant — a "Jarvis" — that I can call by name at
any time and that helps me with everything. Always-on, like Alexa, but **fully
local and private** (no cloud account, no data leaving my LAN).

It grows out of a bigger idea: I have **a lot of ideas and side-projects** that I
discuss with AIs and then forget. I want a system that captures them and treats
each project as a kind of **"agent" / character in a world** — an entity with a
state, a history, and a next step. Jarvis is the **orchestrator** that talks to me
and, over time, can consult and act across these project-agents.

**Core problem being solved:** capture + memory + retrieval of my ideas/projects,
through a low-friction voice interface, so I stop losing my own thoughts.

---

## 2. Hard constraints (non-negotiable)

- **100% free.** No paid API tokens, no subscriptions, no recurring cost. After
  the hardware I already own, running it must cost nothing.
- **Local-first.** Inference runs on my own hardware. No OpenAI/Anthropic/Gemini
  billing. (Free cloud tiers are explicitly out of scope for now — keep it local.)
- **Privacy.** I work in cybersecurity / OT security; data stays on the LAN.
- **Modular.** Each component must be swappable (so I can upgrade pieces later).
- **Start simple, grow deliberately.** MVP first, then layers. Do not over-engineer
  the "world of agents" before the basic loop works.

---

## 3. Hardware & topology (the hybrid design)

Two machines I already own, split by what each is good at:

| Role | Machine | Job |
|------|---------|-----|
| **Ears + Mouth** (always-on) | Raspberry Pi 5, 8GB RAM | Wake word, microphone capture, speech-to-text, text-to-speech. Low power, runs 24/7. |
| **Brain** (on-demand) | Laptop, NVIDIA RTX 3060 **laptop GPU = 6GB VRAM** | Runs the LLM via Ollama (CUDA). Only needs to be on when thinking is required. |

Both are on the **same LAN**. The Pi sends transcribed text to the laptop's Ollama
over the network, gets a response back, and speaks it.

**Why hybrid:** the Pi alone can only run small 3–4B models slowly (~8–12s per
voice round-trip). The laptop GPU gives 1–2s replies with a smarter model. But a
laptop is not a natural always-on appliance (lid/sleep/battery), so the Pi stays
as the always-listening front end and the laptop is the brain it calls.

**Known trade-off to design around:** the laptop must be awake/reachable to answer.
If it's off, the Pi still hears me but has no brain. Acceptable for now; could be
mitigated later with a tiny fallback model on the Pi for trivial commands.

---

## 4. The voice pipeline (the "Alexa magic", broken down)

```
Microphone
  → Wake word detection      (openWakeWord, "hey jarvis")   [on Pi]
  → Record utterance                                         [on Pi]
  → Speech-to-text           (faster-whisper, tiny/base)     [on Pi]
  → Text
  → LLM                      (Ollama, over LAN)              [on Laptop GPU]
  → Response text
  → Text-to-speech           (Piper)                         [on Pi]
  → Speaker
```

**Latency trick:** stream the TTS output sentence-by-sentence while the LLM is
still generating, instead of waiting for the full answer. This sharply cuts
*perceived* latency.

---

## 5. Tech stack (all free / open source)

- **Wake word:** openWakeWord — ships a prebuilt "hey jarvis" model. Runs on the Pi.
- **Speech-to-text:** faster-whisper (tiny or base model on the Pi).
- **LLM runtime:** Ollama on the laptop (CUDA / GPU).
- **Text-to-speech:** Piper.
- **Orchestration:** start with a small custom **Python** service that wires the
  stages together. (Alternative shortcut: Home Assistant "Assist" already wires
  Whisper + Piper + openWakeWord + Ollama via the Wyoming protocol — evaluate it,
  but a custom Python orchestrator keeps the project mine and easy to extend into
  the agent system.)
- **Data store:** SQLite to start (simple, file-based). Could later reuse the
  PostgreSQL instance that already runs on the Pi for IRONLOG.

### Language note (important)
I am a **European Portuguese (pt-PT)** speaker and want to talk to Jarvis in
Portuguese. Please:
- Use a **pt-PT Piper voice** for TTS.
- Configure Whisper for Portuguese (or auto-detect).
- The LLM should respond in European Portuguese by default.

---

## 6. Model choice (for 6GB laptop VRAM)

6GB VRAM comfortably fits a **4B-class** model fully on the GPU, with fast replies.
A 7B model is possible at tighter quantization / partial offload but tighter.

Good 2026 options to try (via Ollama), smaller-to-larger:
- **Gemma 4 (E2B / E4B)** — edge-optimized, fast, light.
- **Qwen3 4B** — strong all-rounder, good multilingual.
- **Phi-3.5 Mini** — solid reasoning for its size.
- **Llama 3.x 3B** — reliable baseline.

Keep the **context window modest** (e.g. 4k) to stay fast. Pick the model
empirically: benchmark a couple on the laptop and keep the best
quality/speed trade-off for Portuguese.

---

## 7. Memory & the "project-agents" design

This is what makes it *mine* rather than just a voice chatbot.

- **Project store:** a table of projects/ideas. Each record holds: `name`,
  `goal`, `status` (idea / exploring / active / paused / dead), `where_i_left_off`,
  `next_step`, `notes`, and links to related AI conversations.
- **Context provider pattern:** each project exposes a small function/endpoint that
  returns its **current state as plain text**. Jarvis injects the relevant
  provider's output into the LLM prompt when I ask about that project. This is the
  seed of the "agent world" — each project is an agent that can report itself, and
  adding a new one is trivial.
- **Low-friction capture is the make-or-break feature.** If logging an idea takes
  more than a few seconds I'll abandon the whole thing. Voice capture like
  *"Jarvis, new idea: ..."* must store it instantly.
- **Retrieval:** start simple (keyword + recency). Add embeddings/RAG later only if
  needed.

**First integration target:** **IRONLOG** — an existing PWA workout tracker
(React/Vite/Tailwind frontend, Node/Express + PostgreSQL backend) that already runs
on the Pi. It becomes the first non-trivial "project-agent" Jarvis can query.

---

## 8. Phased build plan

Build in thin vertical slices; each phase should be runnable before moving on.

- **Phase 0 — Plumbing.** Pi on Raspberry Pi OS Lite (64-bit). Ollama installed on
  the laptop. Confirm the Pi can reach the laptop's Ollama over the LAN (a `curl`
  to the Ollama API returning a completion). Active cooler on the Pi.
- **Phase 1 — Text brain.** A Python script on the Pi: I type a message, it sends
  it to the laptop's Ollama, prints the answer in Portuguese. No voice yet.
- **Phase 2 — Memory.** Add the project store + context-provider pattern. I can ask
  "where did I leave off on X?" and get a real answer from stored state.
- **Phase 3 — Voice loop.** Add openWakeWord → faster-whisper → (existing brain) →
  Piper. Full hands-free round-trip. Add the streaming-TTS latency trick.
- **Phase 4 — First agent.** Wire IRONLOG as a context provider. Then generalize so
  new project-agents can be added cheaply.
- **Phase 5 — Polish.** Robustness, auto-start as a service, error handling, maybe a
  small fallback model on the Pi for offline trivial commands.

---

## 9. Open decisions (flag these, don't silently pick)

1. **Orchestrator:** custom Python service vs Home Assistant Assist.
2. **Data store:** standalone SQLite vs reuse IRONLOG's PostgreSQL on the Pi.
3. **Model:** which 4B-class model gives the best Portuguese quality/speed on 6GB.
4. **IRONLOG placement:** keep it on the Pi (recommended — easy local integration)
   vs move it.

---

## 10. About me (so you calibrate your help)

- Cybersecurity / OT security engineer. Comfortable with: **Python, Node/Express,
  React + Vite + Tailwind, PostgreSQL, Raspberry Pi / Linux home servers,
  Tailscale, REST/WebSockets.** I built IRONLOG (a PWA) from scratch.
- I prefer **simple, guided, well-explained** approaches — especially for anything
  ML-heavy, where my experience is limited.
- Explain trade-offs honestly and don't over-engineer. Keep it free, local, and
  incremental.
```
