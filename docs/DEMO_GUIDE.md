# OpenLLM Studio — recruiter demo runbook

> **Status:** This is a capture plan, not a hosted demo or proof of a fresh live test. Capture screenshots from a locally running instance before adding any images to the README.

## Objective (60 seconds)

Show that this is more than a chatbot UI: it has local model inference, streaming, persisted chats, model switching and backend tests.

## Prepare on Windows

1. Follow [README.md](../README.md#Windows-quick-start-PowerShell) to start Ollama, FastAPI and Streamlit. Install `qwen2.5:1.5b` in Ollama only if needed.
2. Check `http://127.0.0.1:8000/docs` (API docs), then `http://127.0.0.1:8501` (dashboard).
3. Use *fictional* names and prompts. Never record personal chats or API secrets.
4. Screen-record at 1080p if possible; close unrelated windows/notifications first.

## 60-second storyboard

| Seconds | Show | Say |
| --- | --- | --- |
| 0–10 | Dashboard, installed model dropdown | “OpenLLM Studio runs a local model via Ollama; this front end is Streamlit.” |
| 10–22 | Send `Explain Python decorators in two sentences`; show streaming text | “FastAPI streams model output to the UI while tracking successful completion.” |
| 22–35 | Ask `My name is Ada.` followed by `What is my name?` in the same chat | “Previous turns are supplied as context and conversation data is kept in SQLite.” |
| 35–45 | Navigate away, reopen the chat/history | “History survives app restart because storage is server-side, not a temporary UI list.” |
| 45–53 | Show Markdown/JSON export | “I added search and export on top of the base chat workflow.” |
| 53–60 | Show `/docs` or `VALIDATION.md` | “The recorded validation run reported 30 passing tests with mocked Ollama.” |

Do not claim model-switching happened live unless another model is installed and you actually switch it.

## Capture checklist (real images only)

- `docs/screenshots/01-dashboard.png`: clean empty/initial dashboard with model selection
- `docs/screenshots/02-chat-streaming.png`: a completed sample conversation; show the selected model
- `docs/screenshots/03-history.png`: reopened saved conversation or history search
- Optional: `docs/screenshots/04-api-docs.png`: FastAPI Swagger UI

Use **Win + Shift + S** for screenshots or **Win + Alt + R** (Xbox Game Bar where available) for a screen recording. Avoid screenshots showing private local paths, personal chat history, credentials or identifiable notifications. Upload assets only once they exist; do not add broken image links.

## Engineering questions to prepare

**Why SQLite?** Lightweight local persistence without a database server; acceptable for a single-user demo, not a scaled multi-user deployment.

**How does streaming work?** FastAPI emits start/delta/done (or error) NDJSON events; the UI should treat only a done event as a successfully saved turn.

**What does your test result prove?** The [validation record](../VALIDATION.md) reports 30 passing automated tests with Ollama mocked. It does *not* measure live model output quality.

**Current limitations:** No accounts or user authentication, model-dependent output quality and hardware-limited throughput. Keep services bound to loopback.
