import json
import os

import requests
import streamlit as st


API = os.getenv(
    "OPENLLM_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

st.set_page_config(
    page_title="OpenLLM Studio",
    page_icon="✦",
    layout="wide",
)


# ─────────────────────────────────────────────
# App styling
# ─────────────────────────────────────────────

st.markdown(
    """
<style>
:root {
    color-scheme: dark;
    --line: #ffffff1c;
}

html, body, .stApp, button, input, textarea,
[data-baseweb="select"] {
    font-family:
        "Segoe UI Variable Text",
        "Segoe UI",
        Arial,
        sans-serif;
}

.stApp {
    color: #eeeef2;
    background:
        radial-gradient(
            ellipse at 50% 15%,
            #ffffff08,
            transparent 45%
        ),
        #09090b;
}

[data-testid="stHeader"] {
    background: #09090bdd;
    backdrop-filter: blur(20px);
}

.block-container {
    max-width: 1040px;
    padding-top: 2.5rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    font-family:
        "Segoe UI Variable Display",
        "Segoe UI",
        sans-serif !important;
    color: #f4f4f6 !important;
    letter-spacing: -.045em;
    font-weight: 500 !important;
}

h1 { font-size: 2rem !important; }
h2 { font-size: 1.5rem !important; }

[data-testid="stCaptionContainer"] {
    color: #a2a4ad;
}

/* Sidebar */

[data-testid="stSidebar"] {
    background: #111113eb;
    border-right: 1px solid var(--line);
    backdrop-filter: blur(28px);
}

[data-testid="stSidebarUserContent"] {
    padding-top: 1.4rem;
}

[data-testid="stSidebar"] h2 {
    font-size: 1.2rem !important;
}

/* General buttons */

[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button {
    background: linear-gradient(
        145deg,
        #ffffff0c,
        #ffffff03
    );
    color: #e9e9ed;
    border: 1px solid var(--line);
    border-radius: 12px;
    min-height: 2.7rem;
    box-shadow: inset 0 1px #ffffff08;
    transition:
        background .2s,
        transform .2s,
        border-color .2s;
}

[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover {
    color: white;
    border-color: #ffffff65;
    background: #ffffff12;
    transform: translateY(-1px);
}

[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(
        145deg,
        #eeeeef,
        #bdbdc5
    );
    color: #101013;
    border-color: #ffffff88;
}

[data-testid="stSidebar"]
[data-testid="stButton"] button {
    justify-content: flex-start;
    text-align: left;
}

/* General inputs */

[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
    background: #18181d !important;
    color: #efeff4 !important;
    border-color: #ffffff20 !important;
    border-radius: 12px !important;
}

input, textarea {
    color: #f2f2f6 !important;
}

input::placeholder,
textarea::placeholder {
    color: #a6a6b0 !important;
    opacity: 1;
}

/* Chat messages */

[data-testid="stChatMessage"] {
    background: linear-gradient(
        130deg,
        #ffffff08,
        #ffffff02
    );
    border: 1px solid #ffffff12;
    border-radius: 18px;
    padding: 1.2rem;
    margin-bottom: .8rem;
    backdrop-filter: blur(20px);
}

[data-testid="stChatMessage"] p {
    line-height: 1.8;
}

[data-testid="stChatMessageAvatarAssistant"] {
    background: #e8e8ee;
    color: #131316;
}

[data-testid="stChatMessageAvatarUser"] {
    background: #303038;
    color: #eeeeef;
}

[data-testid="stBottom"] > div {
    background: transparent;
}

[data-testid="stBottomBlockContainer"] {
    background: linear-gradient(
        0deg,
        #09090b 70%,
        transparent
    );
}

/* Premium native composer: scoped to studio_prompt */

.st-key-studio_prompt [data-testid="stChatInput"] {
    border: 1px solid transparent;
    border-radius: 22px;

    background:
        linear-gradient(
            145deg,
            #151421f5,
            #0c111cf5
        ) padding-box,
        linear-gradient(
            110deg,
            #9b7de780,
            #775bd780,
            #51c7d980,
            #9b7de780
        ) border-box;

    background-size: 100% 100%, 300% 300%;
    background-position: 0 0, 0% 50%;

    animation:
        studio-composer-border
        18s ease-in-out infinite alternate;

    box-shadow:
        0 10px 34px #00000030,
        inset 0 1px 0 #ffffff06;

    backdrop-filter: blur(22px);
    -webkit-backdrop-filter: blur(22px);

    padding: 8px;

    transition:
        box-shadow 180ms ease,
        border-color 180ms ease;
}

.st-key-studio_prompt
[data-testid="stChatInput"]:focus-within {
    box-shadow:
        0 0 0 2px #b4a0ff60,
        0 0 28px #9375ed25,
        0 10px 34px #00000030;
}

.st-key-studio_prompt [data-baseweb="textarea"],
.st-key-studio_prompt [data-baseweb="textarea"] > div {
    background: transparent !important;
    border: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}

.st-key-studio_prompt
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #f0eff8 !important;

    font-family:
        "Segoe UI Variable Text",
        "Segoe UI",
        Arial,
        sans-serif;

    font-size: 16px;
    font-weight: 400;
    line-height: 1.6;
    letter-spacing: .005em;

    min-height: 56px;
    padding: 10px 12px;
    caret-color: #aee9f3;
}

.st-key-studio_prompt
[data-testid="stChatInput"] textarea::placeholder {
    color: #acadc1 !important;
    opacity: 1;
}

/* Focus is shown around the complete composer. */
.st-key-studio_prompt
[data-testid="stChatInput"] textarea:focus-visible {
    outline: none !important;
}

/* Actual Streamlit send button */

.st-key-studio_prompt
[data-testid="stChatInputSubmitButton"] {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
    flex: 0 0 44px;

    align-self: flex-end;
    margin: 2px;

    border-radius: 14px;
    border: 1px solid #e0ddff50;

    background: linear-gradient(
        135deg,
        #b7a3fa,
        #8edee9
    );

    color: #171525;

    box-shadow:
        0 3px 12px #9478e52b,
        inset 0 1px 0 #ffffff55;

    opacity: 1;

    transition:
        box-shadow 180ms ease,
        filter 180ms ease;
}

.st-key-studio_prompt
[data-testid="stChatInputSubmitButton"]:hover:not(:disabled) {
    color: #171525;
    filter: brightness(1.08);
    box-shadow: 0 0 18px #977ce640;
}

.st-key-studio_prompt
[data-testid="stChatInputSubmitButton"]:focus-visible {
    outline: 3px solid #e1d8ff !important;
    outline-offset: 2px;
}

.st-key-studio_prompt
[data-testid="stChatInputSubmitButton"]:disabled {
    background: #30303f;
    color: #999bad;
    border-color: #ffffff12;
    box-shadow: none;
    opacity: .7;
    cursor: not-allowed;
}

.st-key-studio_prompt
[data-testid="stChatInput"]:has(textarea:disabled) {
    animation: none;
    box-shadow: none;
}

@keyframes studio-composer-border {
    from {
        background-position: 0 0, 0% 50%;
    }

    to {
        background-position: 0 0, 100% 50%;
    }
}

/* Other surfaces */

[data-testid="stExpander"] {
    border-color: #ffffff18;
    border-radius: 12px;
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

hr {
    border-color: #ffffff12;
}

pre, code, code span {
    font-family:
        "Cascadia Code",
        Consolas,
        monospace !important;
}

/* Accessibility */

button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible {
    outline: 3px solid #c0c0ff !important;
    outline-offset: 3px;
}

button:disabled {
    opacity: .5;
}

.brand {
    font-size: .73rem;
    letter-spacing: .22em;
    color: #b8b8c3;
    margin: .4rem 0;
}

.welcome {
    text-align: center;
    margin: -.2rem 0 1.5rem;
}

.welcome h2 {
    font-size: clamp(2rem, 4vw, 3rem) !important;
    line-height: 1.2;
    margin: 0 0 .7rem;
}

.welcome p {
    color: #a5a5b0;
    font-size: 1rem;
    line-height: 1.7;
}

.topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    padding-bottom: .7rem;
    border-bottom: 1px solid #ffffff12;
    margin-bottom: .8rem;
}

.badge {
    font-size: .74rem;
    color: #d3d3dc;
    padding: .35rem .65rem;
    border: 1px solid #ffffff20;
    border-radius: 99px;
    background: #ffffff05;
}

.footnote {
    text-align: center;
    color: #9c9ca8;
    font-size: .75rem;
    padding: 1rem 0;
}

/* Mobile */

@media (max-width: 640px) {
    .block-container {
        padding: 2.5rem 1rem 1rem;
    }

    [data-testid="stChatMessage"] {
        padding: .8rem;
    }

    .st-key-studio_prompt [data-testid="stChatInput"] {
        border-radius: 18px;
        padding: 6px;
    }

    .st-key-studio_prompt
    [data-testid="stChatInput"] textarea {
        padding: 9px 8px;
        min-height: 52px;
        font-size: 16px;
    }
}

/* Reduced motion */

@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
    }

    .st-key-studio_prompt [data-testid="stChatInput"],
    .st-key-studio_prompt
    [data-testid="stChatInputSubmitButton"] {
        animation: none !important;
        transition: none !important;
    }
}

/* Windows high-contrast mode */

@media (forced-colors: active) {
    .st-key-studio_prompt [data-testid="stChatInput"] {
        background: Canvas;
        border: 1px solid CanvasText;
        animation: none;
    }

    .st-key-studio_prompt
    [data-testid="stChatInput"]:focus-within {
        outline: 2px solid Highlight;
    }

    .st-key-studio_prompt
    [data-testid="stChatInputSubmitButton"] {
        background: ButtonFace;
        color: ButtonText;
        border: 1px solid ButtonText;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# 3D particle animation
# ─────────────────────────────────────────────

CORE = """
<!doctype html>
<html>
<head>
<style>
html, body {
    margin: 0;
    background: transparent;
    overflow: hidden;
    height: 260px;
}

canvas {
    width: 100%;
    height: 260px;
    display: block;
}

.mark {
    position: absolute;
    inset: 0;
    display: grid;
    place-items: center;
    pointer-events: none;
}

.mark svg {
    width: 58px;
    height: 58px;
    filter: drop-shadow(0 0 14px #fff9);
}

.beam {
    position: absolute;
    left: calc(50% - 16px);
    top: -80px;
    width: 32px;
    height: 280px;
    background: linear-gradient(
        transparent,
        #ffffff24,
        transparent
    );
    filter: blur(15px);
    pointer-events: none;
    transform: rotate(-9deg);
}
</style>
</head>

<body>
<div class="beam"></div>

<canvas
    id="core"
    role="img"
    aria-label="Rotating three dimensional particle core">
</canvas>

<div class="mark">
    <svg viewBox="0 0 64 64" fill="none" aria-hidden="true">
        <path
            d="M34 5 L54 23 Q57 26 52 28
               L13 38 Q8 40 12 44
               L31 59 L30 9 Q30 3 34 5Z"
            stroke="#f4f4f8"
            stroke-width="2.5"
            stroke-linejoin="round"/>
    </svg>
</div>

<script>
const canvas = document.getElementById("core");
const ctx = canvas.getContext("2d");

const motion = matchMedia(
    "(prefers-reduced-motion: reduce)"
);

let w = 600;
const h = 260;

let rx = 0;
let ry = 0;
let time = 0;
let last = 0;
let frame;
let visible = true;

const points = Array.from({length: 650}, (_, i) => {
    const y = 1 - 2 * (i + .5) / 650;
    const r = Math.sqrt(1 - y * y);
    const a = i * 2.399963;

    return [
        Math.cos(a) * r,
        y,
        Math.sin(a) * r
    ];
});

const stars = Array.from({length: 65}, (_, i) => [
    ((i * 137.508) % 997) / 997,
    ((i * 83.21) % 257) / 257,
    .15 + (i % 5) * .08
]);

function resize() {
    w = innerWidth;

    const d = Math.min(
        devicePixelRatio || 1,
        2
    );

    canvas.width = w * d;
    canvas.height = h * d;
    ctx.setTransform(d, 0, 0, d, 0, 0);
}

function project(x, y, z) {
    const a = time * .16 + rx * .4;
    const b = .35 + ry * .25;

    const xx = x * Math.cos(a) + z * Math.sin(a);
    const zz = -x * Math.sin(a) + z * Math.cos(a);

    const yy = y * Math.cos(b) - zz * Math.sin(b);
    const depth = y * Math.sin(b) + zz * Math.cos(b);

    const scale = 330 / (330 - depth * 85);

    return [
        w / 2 + xx * 91 * scale,
        h / 2 + yy * 91 * scale,
        depth
    ];
}

function draw(ms) {
    if (!motion.matches && visible) {
        time += last
            ? Math.min((ms - last) / 1000, .05)
            : 0;
    }

    last = ms;
    ctx.clearRect(0, 0, w, h);

    stars.forEach(([x, y, a]) => {
        ctx.fillStyle = `rgba(225,225,240,${a})`;
        ctx.fillRect(x * w, y * h, 1, 1);
    });

    const glow = ctx.createRadialGradient(
        w / 2, h / 2, 10,
        w / 2, h / 2, 140
    );

    glow.addColorStop(0, "#ffffff0c");
    glow.addColorStop(1, "#ffffff00");

    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, w, h);

    points
        .map(p => project(...p))
        .sort((a, b) => a[2] - b[2])
        .forEach(([x, y, z]) => {
            const opacity = .12 + (z + 1) * .22;

            ctx.fillStyle =
                `rgba(235,235,245,${opacity})`;

            ctx.beginPath();
            ctx.arc(
                x,
                y,
                .45 + (z + 1) * .34,
                0,
                Math.PI * 2
            );
            ctx.fill();
        });

    for (let ring = 0; ring < 3; ring++) {
        ctx.beginPath();

        for (let j = 0; j <= 180; j++) {
            const a = j / 180 * Math.PI * 2;
            const s = 1.18 + ring * .09;

            const p = project(
                Math.cos(a) * s,
                Math.sin(a) * s * .26,
                Math.sin(a) * s * .84
            );

            if (j === 0) {
                ctx.moveTo(p[0], p[1]);
            } else {
                ctx.lineTo(p[0], p[1]);
            }
        }

        ctx.strokeStyle =
            `rgba(230,230,245,${.13 - ring * .03})`;

        ctx.lineWidth = .6;
        ctx.stroke();
    }

    if (!motion.matches && visible) {
        frame = requestAnimationFrame(draw);
    }
}

function start() {
    cancelAnimationFrame(frame);
    last = 0;
    draw(performance.now());
}

addEventListener("resize", () => {
    resize();
    if (motion.matches) start();
});

addEventListener("pointermove", event => {
    rx = event.clientX / w - .5;
    ry = event.clientY / h - .5;
});

document.addEventListener("visibilitychange", () => {
    visible = !document.hidden;
    start();
});

motion.addEventListener("change", start);

resize();
start();
</script>
</body>
</html>
"""


# ─────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────

def api(method, path, **kwargs):
    response = requests.request(
        method,
        API + path,
        timeout=(5, 190),
        **kwargs,
    )

    if not response.ok:
        try:
            detail = response.json().get(
                "detail",
                "Request failed",
            )
        except ValueError:
            detail = (
                f"Backend returned HTTP "
                f"{response.status_code}"
            )

        raise requests.RequestException(str(detail))

    return response.json()


def select_chat(identifier):
    st.session_state.conversation_id = identifier
    st.session_state.retry_prompt = None
    st.session_state.pending_delete = None
    st.query_params["chat"] = identifier


def reset_chat():
    st.session_state.conversation_id = None
    st.session_state.retry_prompt = None
    st.session_state.pending_delete = None

    if "chat" in st.query_params:
        del st.query_params["chat"]


def delete_chat(identifier):
    api(
        "DELETE",
        "/conversations/" + identifier,
    )

    if st.session_state.conversation_id == identifier:
        reset_chat()

    st.session_state.pending_delete = None


st.session_state.setdefault(
    "conversation_id",
    st.query_params.get("chat"),
)
st.session_state.setdefault("retry_prompt", None)
st.session_state.setdefault("pending_delete", None)


# ─────────────────────────────────────────────
# Load saved conversations
# ─────────────────────────────────────────────

try:
    saved = api("GET", "/conversations")

except (requests.RequestException, ValueError) as exc:
    st.title("OpenLLM Studio")
    st.error(f"Cannot load saved chats: {exc}")
    st.info(
        "Start your FastAPI backend, then reconnect."
    )

    if st.button("Reconnect"):
        st.rerun()

    st.stop()


saved_ids = {chat["id"] for chat in saved}

if st.session_state.conversation_id not in saved_ids:
    st.session_state.conversation_id = None

    if "chat" in st.query_params:
        del st.query_params["chat"]

if st.session_state.pending_delete not in saved_ids:
    st.session_state.pending_delete = None


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="brand">✦ OPENLLM STUDIO</div>',
        unsafe_allow_html=True,
    )

    st.header("Your workspace")

    if st.button(
        "＋ New conversation",
        type="primary",
        use_container_width=True,
    ):
        reset_chat()
        st.rerun()

    search = st.text_input(
        "Search history",
        placeholder="Find a conversation…",
    )

    st.caption(
        f"{len(saved)} saved conversations"
    )

    with st.container(height=300, border=False):
        matches = [
            chat
            for chat in saved
            if search.casefold()
            in chat["title"].casefold()
        ]

        if not matches:
            st.caption(
                "No matching chats."
                if search
                else "Your conversations will appear here."
            )

        for chat in matches:
            identifier = chat["id"]

            active = (
                identifier
                == st.session_state.conversation_id
            )

            chat_column, delete_column = st.columns(
                [5, 1],
                gap="small",
            )

            with chat_column:
                if st.button(
                    ("● " if active else "↗ ")
                    + chat["title"],
                    key=f"history_{identifier}",
                    type=(
                        "primary"
                        if active
                        else "secondary"
                    ),
                    use_container_width=True,
                ):
                    select_chat(identifier)
                    st.rerun()

            with delete_column:
                if st.button(
                    "✕",
                    key=f"remove_{identifier}",
                    help="Delete this conversation",
                    use_container_width=True,
                ):
                    st.session_state.pending_delete = identifier
                    st.rerun()

            if (
                st.session_state.pending_delete
                == identifier
            ):
                st.caption(
                    "Permanently delete this chat?"
                )

                yes_column, cancel_column = st.columns(2)

                if yes_column.button(
                    "Delete",
                    key=f"confirm_remove_{identifier}",
                    use_container_width=True,
                ):
                    try:
                        delete_chat(identifier)
                        st.rerun()

                    except requests.RequestException as exc:
                        st.error(str(exc))

                if cancel_column.button(
                    "Cancel",
                    key=f"cancel_remove_{identifier}",
                    use_container_width=True,
                ):
                    st.session_state.pending_delete = None
                    st.rerun()

    if st.button(
        "↻ Refresh history",
        use_container_width=True,
    ):
        st.rerun()

    st.divider()

    try:
        models = api("GET", "/models")["models"]
        model_error = None

    except (requests.RequestException, ValueError) as exc:
        models = []
        model_error = str(exc)

    model = st.selectbox(
        "Installed Ollama model",
        models,
        disabled=not models,
    )

    if st.button(
        "↻ Refresh models",
        use_container_width=True,
    ):
        st.rerun()

    with st.expander("Generation settings"):
        temperature = st.slider(
            "Creativity",
            0.0,
            2.0,
            0.7,
            0.1,
        )

        memory = st.slider(
            "Previous turns to remember",
            0,
            50,
            10,
        )

    st.caption(
        "Local inference. Your conversations "
        "stay on this computer."
    )


# ─────────────────────────────────────────────
# Open selected conversation
# ─────────────────────────────────────────────

conversation = {
    "title": "New conversation",
    "messages": [],
}

if st.session_state.conversation_id:
    try:
        conversation = api(
            "GET",
            "/conversations/"
            + st.session_state.conversation_id,
        )

    except (requests.RequestException, ValueError) as exc:
        st.error(str(exc))
        st.stop()


status = (
    "● Local model ready"
    if models
    else "○ Model offline"
)

st.markdown(
    '<div class="topline">'
    '<span class="brand">'
    'OPENLLM / PERSONAL INTELLIGENCE'
    '</span>'
    f'<span class="badge">{status}</span>'
    '</div>',
    unsafe_allow_html=True,
)

if model_error:
    st.warning(model_error)

elif not models:
    st.info(
        "No installed models. Start Ollama "
        "and refresh the model list."
    )


# ─────────────────────────────────────────────
# Welcome screen or conversation
# ─────────────────────────────────────────────

messages = conversation["messages"]
suggestion = None

if not messages:
    st.iframe(
        CORE,
        height=260,
        alt="Animated 3D particle core",
    )

    st.markdown(
        """
<div class="welcome">
    <h2>How can I help you today?</h2>
    <p>
        One space for your ideas.
        Powered by your own AI.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.container():
        prompt = st.chat_input(
            "What do you want to explore?",
            key="studio_prompt",
            disabled=not models,
            max_chars=16000,
        )

    labels = [
        "✧ Generate ideas",
        "⌘ Write code",
        "↗ Make a plan",
        "◎ Explain a concept",
    ]

    starter_prompts = [
        (
            "Help me brainstorm an original project idea. "
            "Ask me what interests me first."
        ),
        (
            "Help me write clean code. "
            "Ask me what I want to build first."
        ),
        (
            "Help me make an achievable plan. "
            "Ask me about my goal first."
        ),
        (
            "Help me understand a concept. "
            "Ask me what I want to learn first."
        ),
    ]

    for column, label, seed in zip(
        st.columns(4),
        labels,
        starter_prompts,
    ):
        if column.button(
            label,
            use_container_width=True,
            disabled=not models,
        ):
            suggestion = seed

    st.markdown(
        '<div class="footnote">'
        'Private by design · Saved on your computer'
        ' · No API key'
        '</div>',
        unsafe_allow_html=True,
    )

else:
    st.title("OpenLLM Studio")
    st.caption(conversation["title"])

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Continue the conversation…",
        key="studio_prompt",
        disabled=not models,
        max_chars=16000,
    )


# ─────────────────────────────────────────────
# Export conversation
# ─────────────────────────────────────────────

if st.session_state.conversation_id:
    with st.sidebar:
        st.divider()

        st.download_button(
            "↓ Export this chat",
            data=json.dumps(
                conversation,
                ensure_ascii=False,
                indent=2,
            ),
            file_name=f"chat-{conversation['id']}.json",
            mime="application/json",
            use_container_width=True,
        )


# ─────────────────────────────────────────────
# Retry controls
# ─────────────────────────────────────────────

retry = None

if st.session_state.retry_prompt:
    st.warning(
        "Reply not confirmed. Reload history before "
        "retrying if your connection dropped."
    )

    st.text(st.session_state.retry_prompt)

    retry_column, reload_column = st.columns(2)

    if retry_column.button(
        "Retry last message",
        disabled=not models,
    ):
        retry = st.session_state.retry_prompt

    if reload_column.button("Reload saved history"):
        st.rerun()


# ─────────────────────────────────────────────
# Stream model response
# ─────────────────────────────────────────────

if prompt or suggestion or retry:
    user_text = (
        prompt or suggestion or retry
    ).strip()

    if not user_text:
        st.warning(
            "Enter a message containing text."
        )
        st.stop()

    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        slot = st.empty()
        slot.caption("Thinking…")

        answer = ""
        complete = False

        try:
            with requests.post(
                API + "/chat/stream",
                json={
                    "message": user_text,
                    "conversation_id": (
                        st.session_state.conversation_id
                    ),
                    "model": model,
                    "temperature": temperature,
                    "memory_turns": memory,
                },
                stream=True,
                timeout=(5, 190),
            ) as response:
                if not response.ok:
                    try:
                        detail = response.json().get(
                            "detail",
                            "Generation failed",
                        )
                    except ValueError:
                        detail = (
                            f"Backend returned HTTP "
                            f"{response.status_code}"
                        )

                    raise requests.RequestException(
                        str(detail)
                    )

                for line in response.iter_lines(
                    chunk_size=1,
                ):
                    if not line:
                        continue

                    event = json.loads(line)
                    kind = event["type"]

                    if kind == "start":
                        select_chat(
                            event["conversation_id"]
                        )

                    elif kind == "delta":
                        answer += event["content"]
                        slot.markdown(answer + " ▌")

                    elif kind == "error":
                        raise requests.RequestException(
                            event.get(
                                "message",
                                "Generation failed",
                            )
                        )

                    elif kind == "done":
                        complete = True

                if not complete:
                    raise requests.RequestException(
                        "The reply stream was interrupted."
                    )

            st.session_state.retry_prompt = None
            st.rerun()

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ) as exc:
            slot.markdown(
                answer or "No reply received."
            )
            st.error(str(exc))

            st.caption(
                "Partial text is a preview, "
                "not a saved completed reply."
            )

            st.session_state.retry_prompt = user_text

            if st.button("Continue / reload history"):
                st.rerun()