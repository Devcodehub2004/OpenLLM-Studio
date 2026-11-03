"""Local AI workspace: chat, reusable work prompts, and conversation history."""

import json
import os
from datetime import datetime
from html import escape
from pathlib import Path

import requests
import streamlit as st

API = os.getenv("OPENLLM_API_URL", "http://127.0.0.1:8000").rstrip("/")
st.set_page_config(page_title="OpenLLM Studio", page_icon="✦", layout="wide")
st.markdown(
    f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)

# Original, code-native workspace mark. All decorative artwork stays local.
MARK = '<span class="studio-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>'
ICONS = {
    "Plan": '<rect x="5" y="5" width="14" height="16" rx="2"/><path d="M9 3h6v4H9zM9 12h6M9 16h4"/>',
    "Write": '<path d="m15 4 5 5-11 11H4v-5ZM12 7l5 5M4 4h5M4 9h2"/>',
    "Analyze": '<path d="M4 20h17M7 16v-5M12 16V5M17 16V8"/>',
    "Code": '<path d="m8 7-5 5 5 5m8-10 5 5-5 5M14 4l-4 16"/>',
}
PROMPTS = [
    {"id": "project", "category": "Plan", "title": "Turn a goal into a plan",
     "description": "Go from a big idea to clear milestones and next steps.",
     "prompt": "Help me build an actionable project plan for [goal]. Ask about my timeline, constraints, and desired outcome first. Then break the work into milestones, deliverables, risks, and a checklist of next steps."},
    {"id": "draft", "category": "Write", "title": "Find the right words",
     "description": "Create a thoughtful first draft, ready to make your own.",
     "prompt": "Help me draft [an email, proposal, or document] about [topic] for [audience]. Ask me about the main message, tone, and context first. Write a clear draft, then help me refine it."},
    {"id": "insights", "category": "Analyze", "title": "Make sense of information",
     "description": "Find the key takeaways, patterns, and what matters next.",
     "prompt": "Help me analyze the information I will paste next. Ask what decision I need to make first. Then summarize the key facts, identify patterns and gaps, and suggest next steps. Distinguish facts from assumptions."},
    {"id": "build", "category": "Code", "title": "Build something useful",
     "description": "Work through an idea, implementation, and verification.",
     "prompt": "Help me implement [feature or project] in [language or framework]. Ask about the requirements and existing code first. Then propose an approach, work through the implementation, and explain how to verify it."},
    {"id": "meeting", "category": "Plan", "title": "Bring clarity to a meeting",
     "description": "Turn your notes into decisions, owners, and actions.",
     "prompt": "Turn the meeting notes I will paste next into a concise summary, decisions made, open questions, and action items with owners and due dates. Mark missing owners or dates as unspecified rather than inventing them."},
    {"id": "polish", "category": "Write", "title": "Give your draft a polish",
     "description": "Make your writing clearer without losing your voice.",
     "prompt": "Help me improve the draft I will paste next. Ask about the audience and tone first. Suggest a clearer version that preserves my meaning, and briefly explain the most useful edits."},
    {"id": "compare", "category": "Analyze", "title": "Think through a decision",
     "description": "Compare your options with tradeoffs you can act on.",
     "prompt": "Help me compare [options] for [decision]. Ask about my priorities and constraints first. Create a comparison table, explain the tradeoffs and uncertainties, and recommend a next step based on my criteria."},
    {"id": "debug", "category": "Code", "title": "Get unstuck on a bug",
     "description": "Find the cause and work toward a reliable fix.",
     "prompt": "Help me debug a problem. Ask for the relevant code, error message, expected behavior, and steps to reproduce first. Explain likely causes, suggest a focused fix, and show me how to check for regressions."},
]


def api(method, path, **kwargs):
    response = requests.request(method, API + path, timeout=(5, 190), **kwargs)
    if not response.ok:
        try:
            detail = response.json().get("detail", "Request failed")
        except ValueError:
            detail = f"Backend returned HTTP {response.status_code}"
        raise requests.RequestException(str(detail))
    return response.json()


def select_chat(identifier):
    st.session_state.conversation_id = identifier
    st.session_state.retry_prompt = None
    st.session_state.pending_delete = None
    st.session_state.workspace_view = "Chat"
    st.session_state.studio_prompt = ""
    st.query_params["chat"] = identifier


def reset_chat():
    st.session_state.conversation_id = None
    st.session_state.retry_prompt = None
    st.session_state.pending_delete = None
    st.session_state.workspace_view = "Chat"
    st.session_state.studio_prompt = ""
    if "chat" in st.query_params:
        del st.query_params["chat"]


def use_prompt(text):
    # Prefill rather than submit: users can replace placeholders before sending.
    reset_chat()
    st.session_state.studio_prompt = text


def delete_chat(identifier):
    api("DELETE", "/conversations/" + identifier)
    if st.session_state.conversation_id == identifier:
        reset_chat()
    st.session_state.pending_delete = None


def display_date(value):
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y")
    except (ValueError, TypeError):
        return "Saved conversation"


def markdown_export(conversation):
    parts = [f"# {conversation['title']}"]
    for message in conversation["messages"]:
        role = "You" if message["role"] == "user" else "Assistant"
        parts.append(f"## {role}\n\n{message['content']}")
    return "\n\n".join(parts) + "\n"


def prompt_card(item, prefix):
    category = item["category"]
    with st.container(border=True, key=f"prompt_card_{prefix}_{item['id']}"):
        st.markdown(
            f'<div class="category-icon {category.lower()}">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" aria-hidden="true">{ICONS[category]}</svg></div>'
            f'<span class="card-category">{category}</span>'
            f'<h3 class="card-title">{item["title"]}</h3>'
            f'<p class="card-description">{item["description"]}</p>',
            unsafe_allow_html=True,
        )
        st.button(
            "Use prompt", key=f"use_{prefix}_{item['id']}",
            icon=":material/arrow_forward:", use_container_width=True,
            on_click=use_prompt, args=(item["prompt"],),
        )


st.session_state.setdefault("conversation_id", st.query_params.get("chat"))
st.session_state.setdefault("retry_prompt", None)
st.session_state.setdefault("pending_delete", None)
st.session_state.setdefault("workspace_view", "Chat")

try:
    saved = api("GET", "/conversations")
except (requests.RequestException, ValueError) as exc:
    st.title("OpenLLM Studio")
    st.error(f"Cannot load saved chats: {exc}")
    st.info("Start your FastAPI backend, then reconnect.")
    if st.button("Reconnect", icon=":material/refresh:"):
        st.rerun()
    st.stop()

saved_ids = {chat["id"] for chat in saved}
if st.session_state.conversation_id not in saved_ids:
    st.session_state.conversation_id = None
    if "chat" in st.query_params:
        del st.query_params["chat"]
if st.session_state.pending_delete not in saved_ids:
    st.session_state.pending_delete = None

try:
    models = api("GET", "/models")["models"]
    model_error = None
except (requests.RequestException, ValueError) as exc:
    models, model_error = [], str(exc)

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">{MARK}<div>OpenLLM <strong>Studio</strong>'
        '<small>Your everyday AI workspace</small></div></div>', unsafe_allow_html=True,
    )
    st.button("New chat", icon=":material/add:", type="primary",
              use_container_width=True, on_click=reset_chat, key="new_chat")
    st.radio("Workspace", ["Chat", "Prompt library", "History"],
             key="workspace_view", label_visibility="collapsed",
             format_func=lambda view: {"Chat": "Chat", "Prompt library": "Prompt library",
                                       "History": "Conversation history"}[view])
    st.divider()
    st.markdown('<div class="rail-label">RECENT CHATS</div>', unsafe_allow_html=True)
    with st.container(key="recent_chats"):
        if not saved:
            st.caption("A fresh start. Your chats will appear here as you work.")
        for chat in saved[:5]:
            st.button(chat["title"], key=f"recent_{chat['id']}", icon=":material/chat_bubble_outline:",
                      type="secondary", use_container_width=True,
                      on_click=select_chat, args=(chat["id"],))
    st.divider()
    with st.expander("Model & preferences", icon=":material/tune:", expanded=False):
        model = st.selectbox("Installed Ollama model", models, disabled=not models, key="selected_model")
        temperature = st.slider("Creativity", 0.0, 2.0, 0.7, 0.1, key="creativity")
        memory = st.slider("Previous turns to remember", 0, 50, 10, key="memory")
        if st.button("Refresh models", icon=":material/refresh:", use_container_width=True):
            st.rerun()
    st.markdown(
        '<div class="privacy-note"><span class="privacy-dot"></span>'
        '<div><strong>Made for your space</strong><br>'
        'Local models. Chats saved on this computer.</div></div>', unsafe_allow_html=True,
    )

view = st.session_state.workspace_view
status = "Local model ready" if models else "Model unavailable"
st.markdown(
    '<div class="workspace-topbar"><div><span class="workspace-name">Workspace</span>'
    f'<span class="breadcrumb">/</span><strong>{view}</strong></div>'
    f'<span class="status-pill {"ready" if models else "offline"}">'
    f'<span aria-hidden="true"></span>{status}</span></div>', unsafe_allow_html=True,
)
if model_error:
    st.warning(model_error)
elif not models:
    st.info("No installed models. Start Ollama and refresh the model list in Model & preferences.")

conversation = {"title": "New conversation", "messages": []}
if st.session_state.conversation_id:
    try:
        conversation = api("GET", "/conversations/" + st.session_state.conversation_id)
    except (requests.RequestException, ValueError) as exc:
        st.error(str(exc))
        st.stop()

if view == "Prompt library":
    st.markdown('<div class="page-eyebrow">A LITTLE INSPIRATION</div>', unsafe_allow_html=True)
    st.title("A starting point for great work")
    st.write("Pick a prompt, make it yours, and take the next step.")
    category = st.radio("Filter prompts", ["All", "Plan", "Write", "Analyze", "Code"],
                        horizontal=True, key="prompt_category")
    filtered = [item for item in PROMPTS if category == "All" or item["category"] == category]
    for start in range(0, len(filtered), 4):
        for column, item in zip(st.columns(4), filtered[start:start + 4]):
            with column:
                prompt_card(item, "library")
    st.caption("Prompts open in a new chat. Replace the bracketed details before sending.")
    st.stop()

if view == "History":
    st.markdown('<div class="page-eyebrow">PICK UP WHERE YOU LEFT OFF</div>', unsafe_allow_html=True)
    st.title("Your conversations")
    st.write("Good ideas deserve a place to come back to.")
    search_column, refresh_column = st.columns([4, 1], vertical_alignment="bottom")
    search = search_column.text_input("Search history", placeholder="Find a conversation…", key="history_search")
    if refresh_column.button("Refresh", icon=":material/refresh:", use_container_width=True):
        st.rerun()
    matches = [chat for chat in saved if search.casefold() in chat["title"].casefold()]
    st.caption(f"{len(matches)} of {len(saved)} saved conversations")
    if not matches:
        st.info("No matching chats. Try another search." if search else "Your next idea starts with a new chat.")
    for chat in matches:
        with st.container(border=True, key=f"history_card_{chat['id']}"):
            details, open_column, delete_column = st.columns([5, 1.3, 1.3], vertical_alignment="center")
            details.text(chat["title"])
            details.caption(display_date(chat.get("updated_at")))
            open_column.button("Open", key=f"open_{chat['id']}", use_container_width=True,
                               on_click=select_chat, args=(chat["id"],))
            if delete_column.button("Delete", key=f"delete_{chat['id']}", use_container_width=True):
                st.session_state.pending_delete = chat["id"]
            if st.session_state.pending_delete == chat["id"]:
                st.warning(f"Permanently delete “{chat['title']}” and its messages?")
                confirm, cancel = st.columns(2)
                if confirm.button("Delete permanently", key=f"confirm_{chat['id']}"):
                    try:
                        delete_chat(chat["id"])
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(str(exc))
                if cancel.button("Keep conversation", key=f"cancel_{chat['id']}"):
                    st.session_state.pending_delete = None
                    st.rerun()
    st.stop()

messages = conversation["messages"]
if not messages:
    st.markdown(
        f'<div class="welcome">{MARK}<div class="hero-eyebrow">YOUR SPACE TO MAKE PROGRESS</div>'
        '<h1>How can I help you today?</h1>'
        '<p>From the first idea to the final detail.<br>Let’s do your best work, together.</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="home_composer"):
        prompt = st.chat_input("Describe a task, ask a question, or explore an idea…",
                               key="studio_prompt", disabled=not models, max_chars=16000)
        st.markdown(
            '<div class="composer-meta"><span>Think it through. Make it happen.</span>'
            f'<span>{escape(model or "Select a local model")} · Local</span></div>', unsafe_allow_html=True,
        )
    st.markdown('<div class="section-label">A little inspiration to get you started</div>', unsafe_allow_html=True)
    for column, item in zip(st.columns(4), PROMPTS[:4]):
        with column:
            prompt_card(item, "home")
    with st.container(key="home_footer"):
        st.button("Explore all prompts", icon=":material/arrow_forward:",
                  on_click=lambda: st.session_state.update(workspace_view="Prompt library"))
        st.caption("Your conversations stay on this computer. AI can make mistakes; review important details.")
else:
    title_column, export_column = st.columns([4, 1], vertical_alignment="center")
    title_column.title(conversation["title"])
    title_column.caption(f"{model or 'No model selected'} · {memory} previous turns of context")
    with export_column.popover("Export chat", icon=":material/download:", use_container_width=True):
        st.download_button("Download Markdown", markdown_export(conversation),
                           file_name=f"chat-{conversation['id']}.md", mime="text/markdown",
                           use_container_width=True)
        st.download_button("Download JSON", json.dumps(conversation, ensure_ascii=False, indent=2),
                           file_name=f"chat-{conversation['id']}.json", mime="application/json",
                           use_container_width=True)
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("model"):
                st.caption(message["model"])
    prompt = st.chat_input("Ask a follow-up or take the next step…", key="studio_prompt",
                           disabled=not models, max_chars=16000)

retry = None
if st.session_state.retry_prompt:
    st.warning("Reply not confirmed. Reload history before retrying if your connection dropped.")
    st.text(st.session_state.retry_prompt)
    retry_column, reload_column = st.columns(2)
    if retry_column.button("Retry last message", disabled=not models):
        retry = st.session_state.retry_prompt
    if reload_column.button("Reload saved history"):
        st.rerun()

if prompt or retry:
    user_text = (prompt or retry).strip()
    if not user_text:
        st.warning("Enter a message containing text.")
        st.stop()
    with st.chat_message("user"):
        st.markdown(user_text)
    with st.chat_message("assistant"):
        slot = st.empty()
        slot.caption("Thinking…")
        answer, complete = "", False
        try:
            with requests.post(
                API + "/chat/stream", stream=True, timeout=(5, 190),
                json={"message": user_text, "conversation_id": st.session_state.conversation_id,
                      "model": model, "temperature": temperature, "memory_turns": memory},
            ) as response:
                if not response.ok:
                    try:
                        detail = response.json().get("detail", "Generation failed")
                    except ValueError:
                        detail = f"Backend returned HTTP {response.status_code}"
                    raise requests.RequestException(str(detail))
                for line in response.iter_lines(chunk_size=1):
                    if not line:
                        continue
                    event = json.loads(line)
                    if event["type"] == "start":
                        # No widget state changes during generation: the composer already exists.
                        st.session_state.conversation_id = event["conversation_id"]
                        st.query_params["chat"] = event["conversation_id"]
                    elif event["type"] == "delta":
                        answer += event["content"]
                        slot.markdown(answer + " ▌")
                    elif event["type"] == "error":
                        raise requests.RequestException(event.get("message", "Generation failed"))
                    elif event["type"] == "done":
                        complete = True
                if not complete:
                    raise requests.RequestException("The reply stream was interrupted.")
            st.session_state.retry_prompt = None
            st.rerun()
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            slot.markdown(answer or "No reply received.")
            st.error(str(exc))
            st.caption("Partial text is a preview, not a saved completed reply.")
            st.session_state.retry_prompt = user_text
            if st.button("Continue / reload history"):
                st.rerun()
