"""
Streamlit RAG Chat Application
Interactive chat interface with OpenAI vector stores
"""

import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from datetime import date

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:
    get_script_run_ctx = None


def _read_env_var_from_file(path: str, key: str) -> str | None:
    """Lightweight fallback to read a KEY=VALUE pair from a .env file without logging values."""
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith(key + "="):
                    continue
                value = line.split("=", 1)[1].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                    value = value[1:-1].strip()
                return value
    except Exception:
        return None

    return None


# Load environment variables (project .env should override any OS-level vars)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

ENV_PATH = os.path.join(PARENT_DIR, ".env")
if not os.path.exists(ENV_PATH):
    ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH, override=True)

if __name__ == "__main__" and get_script_run_ctx is not None and get_script_run_ctx() is None:
    print("This is a Streamlit app. Run it with:")
    print("  streamlit run streamlit_app.py")
    raise SystemExit(0)

api_key = os.getenv("OPENAI_API_KEY")

def _get_openai_api_key_from_secrets() -> str | None:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            v = st.secrets.get("OPENAI_API_KEY")
            return str(v).strip() if v else None

        if "openai" in st.secrets:
            section = st.secrets.get("openai")
            if isinstance(section, dict):
                v = section.get("api_key") or section.get("OPENAI_API_KEY")
                return str(v).strip() if v else None
        if "OPENAI" in st.secrets:
            section = st.secrets.get("OPENAI")
            if isinstance(section, dict):
                v = section.get("api_key") or section.get("OPENAI_API_KEY")
                return str(v).strip() if v else None
    except Exception:
        return None
    return None


# Try to override with Streamlit secrets if configured (e.g. on Streamlit Cloud)
secrets_api_key = _get_openai_api_key_from_secrets()
if secrets_api_key:
    api_key = secrets_api_key

# Final fallback: read directly from the .env file if nothing else is set
if not api_key:
    file_api_key = _read_env_var_from_file(ENV_PATH, "OPENAI_API_KEY")
    if file_api_key:
        api_key = file_api_key

if not api_key:
    st.error(
        "OPENAI_API_KEY is not set. For local runs, add it to your .env file. "
        "For Streamlit Cloud, define OPENAI_API_KEY in Settings → Secrets."
    )
    st.stop()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

MAX_GUEST_QUERIES_PER_DAY = 25
_guest_quota_by_id = {}

# Page configuration
st.set_page_config(
    page_title="Pentecost University | AI Knowledge Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    :root {
        --brand: #0b3d91;
        --brand-2: #0a2a63;
        --accent: #f5b301;
        --bg: #020617;
        --panel: #020617;
        --border: rgba(148, 163, 184, 0.35);
        --text: #e5e7eb;
        --muted: rgba(148, 163, 184, 0.82);
    }

    .main {
        padding: 1.75rem 2.25rem;
        background: var(--bg);
    }

    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }

    h1, h2, h3, h4 {
        color: var(--text);
        letter-spacing: -0.02em;
    }

    .pu-hero {
        background: linear-gradient(135deg, rgba(11, 61, 145, 0.10), rgba(245, 179, 1, 0.08));
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem 1.35rem;
        margin-bottom: 1rem;
    }

    .pu-hero-title {
        font-size: 1.55rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }

    .pu-hero-subtitle {
        margin: 0.35rem 0 0 0;
        color: var(--muted);
        font-size: 0.98rem;
        line-height: 1.35;
    }

    .pu-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        background: rgba(245, 179, 1, 0.16);
        border: 1px solid rgba(245, 179, 1, 0.28);
        color: var(--text);
        font-weight: 700;
        font-size: 0.8rem;
        margin-top: 0.75rem;
    }

    .pu-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.95rem 1rem;
        margin: 0.75rem 0;
    }

    .kb-files-title {
        margin: 1rem 0 0.5rem 0;
        font-size: 1.35rem;
        font-weight: 800;
        line-height: 1.2;
        color: var(--text);
    }

    .stChatMessage {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
    }

    /* Ensure all markdown text (including assistant answers, hero copy, etc.)
       uses the light text color for readability on dark background. */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        color: var(--text);
    }

    .stChatMessage [data-testid="stMarkdownContainer"] p {
        line-height: 1.6;
        font-size: 0.98rem;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid var(--border);
        background: #020617;
        box-shadow: 0 1px 0 rgba(15, 23, 42, 0.5);
        color: var(--text);
    }

    [data-testid="stChatMessage"][data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: rgba(15, 23, 42, 0.9);
    }

    .st-emotion-cache-1v0mbdj {
        border-radius: 10px;
    }

    h1 {
        color: var(--brand);
        font-weight: 700;
    }

    [data-testid="stSidebar"] {
        border-right: 1px solid var(--border);
        background: #020617;
        color: var(--text);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
    }

    [data-testid="stButton"] button {
        border-radius: 12px;
        border: 1px solid var(--border);
        padding: 0.55rem 0.85rem;
        font-weight: 650;
    }

    [data-testid="stButton"] button:hover {
        border-color: rgba(11, 61, 145, 0.30);
        background: rgba(11, 61, 145, 0.05);
    }

    [data-testid="stChatInput"] {
        border-top: 1px solid var(--border);
        padding-top: 0.5rem;
    }

    [data-testid="stChatInput"] textarea {
        border-radius: 14px;
        border: 1px solid var(--border);
        background: #020617;
        color: var(--text);
    }

    .stAlert {
        border-radius: 10px;
    }

    .vector-store-info {
        background-color: var(--panel);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid var(--brand);
        margin-bottom: 1rem;
        color: var(--text);
    }

    .vector-store-info strong {
        color: var(--text);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Initialize and return OpenAI client"""
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Get model from env, with fallback for Assistants API compatibility
# Cost-focused default: gpt-3.5-turbo
env_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# List of models supported by Assistants API
SUPPORTED_ASSISTANT_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-4",
    "gpt-3.5-turbo"
]

# Use a compatible model for Assistants API
if env_model not in SUPPORTED_ASSISTANT_MODELS:
    # Fallback to gpt-3.5-turbo if the env model is not supported
    st.warning(f"Model '{env_model}' not supported. Using 'gpt-3.5-turbo'.")
    model_chat = "gpt-3.5-turbo"
else:
    model_chat = env_model

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "selected_vector_store" not in st.session_state:
    st.session_state.selected_vector_store = None

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "guest_daily_count" not in st.session_state:
    st.session_state.guest_daily_count = 0

if "guest_daily_date" not in st.session_state:
    st.session_state.guest_daily_date = date.today().isoformat()

if "guest_id" not in st.session_state:
    st.session_state.guest_id = None

# Fetch vector stores
@st.cache_data(ttl=60)
def fetch_vector_stores():
    """Fetch all available vector stores"""
    try:
        vector_stores = client.vector_stores.list()
        return vector_stores.data
    except Exception as e:
        st.error(f"Error fetching vector stores: {e}")
        return []


@st.cache_data(ttl=60)
def fetch_vector_store_files(vector_store_id: str):
    try:
        files = client.vector_stores.files.list(vector_store_id=vector_store_id)
        return getattr(files, "data", [])
    except Exception as e:
        st.error(f"Error fetching vector store files: {e}")
        return []


@st.cache_data(ttl=60)
def fetch_vector_store_filenames_and_types(vector_store_id: str):
    attached_files = fetch_vector_store_files(vector_store_id)
    filenames: list[str] = []
    extensions: set[str] = set()

    for vf in attached_files:
        fid = getattr(vf, "id", None)
        if not fid:
            continue
        try:
            f = client.files.retrieve(fid)
            filename = getattr(f, "filename", None)
            if not filename:
                continue
            filenames.append(filename)
            ext = os.path.splitext(filename)[1].lower().lstrip(".")
            if ext:
                extensions.add(ext)
        except Exception:
            continue

    file_types_summary = None
    if extensions:
        file_types_summary = ", ".join(sorted({e.upper() for e in extensions}))

    return sorted(set(filenames)), file_types_summary

# Create assistant
def create_assistant(vector_store_id, vector_store_name, file_types_summary: str | None = None):
    """Create an OpenAI assistant with file search capability"""
    try:
        file_types_line = ""
        if file_types_summary:
            file_types_line = f"\n\nThis knowledge base contains the following file types: {file_types_summary}."

        assistant = client.beta.assistants.create(
            name=f"Assistant for {vector_store_name}",
            instructions=f"""You are a knowledgeable AI assistant with access to documents in the '{vector_store_name}' knowledge base.
            {file_types_line}
            
Your role is to:
- Strictly provide accurate, detailed answers based on the documents in the knowledge base only and nothing else.
- Strictly decline to answer any questions that are not related to the documents in the knowledge base except for when the user ask for links to the documents.
- Your response should be well crafted and easy to understand.
- You should also be ready to walk users through the documents in the knowledge base step by step steadily
-Always prioritize accuracy and cite your sources when answering questions.""",

            model=model_chat,
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }
        )
        return assistant.id
    except Exception as e:
        st.error(f"Error creating assistant: {e}")
        return None

# Create thread
def create_thread():
    """Create a new conversation thread"""
    try:
        thread = client.beta.threads.create()
        return thread.id
    except Exception as e:
        st.error(f"Error creating thread: {e}")
        return None


def _is_link_request(user_message: str) -> bool:
    msg = (user_message or "").strip().lower()
    if not msg:
        return False

    triggers = (
        "link",
        "links",
        "url",
        "urls",
        "source",
        "sources",
        "view source",
        "download",
        "where can i find",
        "where can i get",
    )
    return any(t in msg for t in triggers)


def _build_knowledge_base_links_block(vector_store_id: str) -> str:
    try:
        attached_files = client.vector_stores.files.list(vector_store_id=vector_store_id)
        data = getattr(attached_files, "data", []) or []
    except Exception:
        data = []

    links: list[tuple[str, str]] = []
    for vf in data:
        fid = getattr(vf, "id", None)
        if not fid:
            continue

        filename = None
        try:
            f = client.files.retrieve(fid)
            filename = getattr(f, "filename", None)
        except Exception:
            filename = None

        try:
            vs_file = client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=fid,
            )
            attrs = getattr(vs_file, "attributes", None) or {}
            if not isinstance(attrs, dict):
                continue
            display_name = attrs.get("doc") or filename
            url = attrs.get("view_source_url") or attrs.get("source_url")
            if display_name and url:
                links.append((display_name, url))
        except Exception:
            continue

    if not links:
        return ""

    unique = []
    seen = set()
    for name, url in sorted(links, key=lambda x: (x[0], x[1])):
        key = (name, url)
        if key in seen:
            continue
        seen.add(key)
        unique.append((name, url))

    lines = [f"- [View source: {name}]({url})" for name, url in unique]
    return "\n\n**Document links:**\n" + "\n".join(lines)

# Get assistant response
def get_assistant_response(thread_id, assistant_id, user_message, vector_store_id):
    """Get response from the assistant"""
    try:
        # Add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Wait for completion with progress indicator
        with st.spinner("🤔 Thinking..."):
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(0.5)
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
        
        if run.status == 'completed':
            # Retrieve messages
            messages = client.beta.threads.messages.list(thread_id=thread_id)

            # Get the latest assistant message and collect any file citations
            latest_assistant = None
            for message in messages.data:
                if message.role == "assistant":
                    latest_assistant = message
                    break

            if not latest_assistant:
                return "I couldn't generate a response. Please try again."

            full_text = ""
            source_file_ids = set()

            for content in latest_assistant.content:
                if content.type != "text":
                    continue
                text_obj = content.text
                full_text += text_obj.value

                # Collect file IDs from annotations (file_citation or file_path)
                annotations = getattr(text_obj, "annotations", []) or []
                for ann in annotations:
                    file_id = None
                    file_citation = getattr(ann, "file_citation", None)
                    if file_citation is not None:
                        file_id = getattr(file_citation, "file_id", None)
                    file_path = getattr(ann, "file_path", None)
                    if file_path is not None and not file_id:
                        file_id = getattr(file_path, "file_id", None)
                    if file_id:
                        source_file_ids.add(file_id)

            if not full_text:
                return "I couldn't generate a response. Please try again."

            # Resolve file IDs to document names + source URLs (if present on vector store file attributes)
            sources: list[tuple[str, str | None]] = []
            for fid in source_file_ids:
                filename = None
                try:
                    f = client.files.retrieve(fid)
                    filename = getattr(f, "filename", None)
                except Exception:
                    filename = None

                source_url = None
                doc_title = None
                if vector_store_id:
                    try:
                        vs_file = client.vector_stores.files.retrieve(
                            vector_store_id=vector_store_id,
                            file_id=fid,
                        )
                        attrs = getattr(vs_file, "attributes", None) or {}
                        if isinstance(attrs, dict):
                            doc_title = attrs.get("doc")
                            source_url = attrs.get("view_source_url") or attrs.get("source_url")
                    except Exception:
                        source_url = None

                display_name = doc_title or filename
                if display_name:
                    sources.append((display_name, source_url))

            if sources:
                unique = []
                seen = set()
                for name, url in sorted(sources, key=lambda x: (x[0], x[1] or "")):
                    key = (name, url or "")
                    if key in seen:
                        continue
                    seen.add(key)
                    unique.append((name, url))

                lines = []
                for name, url in unique:
                    if url:
                        lines.append(f"- [View source: {name}]({url})")
                    else:
                        lines.append(f"- {name}")

                sources_block = "\n\n**Sources:**\n" + "\n".join(lines)
                full_text += sources_block

            if vector_store_id and _is_link_request(user_message):
                kb_links_block = _build_knowledge_base_links_block(vector_store_id)
                if kb_links_block:
                    full_text += kb_links_block

            return full_text
        if run.status == 'failed':
            return "Error: The assistant run failed. Please try again."

        if run.status == 'cancelled':
            return "Error: The assistant run was cancelled. Please try again."

        if run.status == 'expired':
            return "Error: The assistant run expired. Please try again."

        if run.status == 'requires_action':
            return "Error: The assistant requires additional action to continue."

        return f"Error: Run ended with status {run.status}"
            
    except Exception as e:
        return f"Error getting response: {str(e)}"

def reset_chat_session():
    """Reset the chat session by creating a new thread and clearing messages."""
    st.session_state.messages = []
    st.session_state.thread_id = create_thread()


def handle_user_prompt(prompt: str):
    """Handle a user prompt (typed or suggested) and append assistant response."""
    if st.session_state.user_role == "guest":
        guest_id = st.session_state.get("guest_id")
        if not guest_id:
            st.error("Guest ID is missing. Please reload the app and log in again as guest.")
            return
        today_str = date.today().isoformat()
        key = (guest_id, today_str)
        used = _guest_quota_by_id.get(key, 0)
        if used >= MAX_GUEST_QUERIES_PER_DAY:
            st.warning("Guest limit reached for today (25 queries). Please come back tomorrow or use admin access.")
            return
        _guest_quota_by_id[key] = used + 1
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = get_assistant_response(
            st.session_state.thread_id,
            st.session_state.assistant_id,
            prompt,
            st.session_state.selected_vector_store,
        )
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})

if st.session_state.user_role is None:
    st.markdown("### Access")
    role_choice = st.radio("Choose how to use the assistant:", ["Guest", "Admin"])
    if role_choice == "Admin":
        password_input = st.text_input("Admin password", type="password")
        if st.button("Login"):
            if not ADMIN_PASSWORD:
                st.error("Admin password is not configured in the environment.")
            elif password_input == ADMIN_PASSWORD:
                st.session_state.user_role = "admin"
                st.success("Logged in as admin.")
                st.rerun()
            else:
                st.error("Incorrect admin password.")
    else:
        guest_id_input = st.text_input("Guest ID (e.g., student index number)")
        if st.button("Continue as guest"):
            guest_id_input = guest_id_input.strip()
            if not guest_id_input:
                st.error("Please enter a guest ID before continuing.")
            else:
                st.session_state.user_role = "guest"
                st.session_state.guest_id = guest_id_input
                st.rerun()
    st.stop()

# Sidebar
with st.sidebar:
    st.markdown(
        """
        <div class="pu-card">
            <div style="font-weight:800; font-size:1.05rem; color: var(--text);">Pentecost University</div>
            <div style="color: var(--muted); margin-top: 0.15rem; font-size:0.92rem;">
                RAG Proof of Concept
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.title("⚙️ Settings")
    
    # Fetch vector stores
    vector_stores = fetch_vector_stores()
    
    if vector_stores:
        st.subheader("📚 Available Knowledge Bases")
        
        # Create a dictionary for vector store selection
        vector_store_options = {vs.name: vs for vs in vector_stores}
        
        selected_store_name = st.selectbox(
            "Select a knowledge base:",
            options=list(vector_store_options.keys()),
            help="Choose which knowledge base to query"
        )
        
        selected_store = vector_store_options[selected_store_name]
        st.session_state.selected_store_name = selected_store.name
        
        # Display vector store info
        st.markdown(f"""
        <div class="vector-store-info">
            <strong>📊 Store Details</strong><br>
            <strong>Name:</strong> {selected_store.name}<br>
            <strong>Files:</strong> {selected_store.file_counts.total}<br>
            <strong>Status:</strong> {selected_store.status}
        </div>
        """, unsafe_allow_html=True)

        st.subheader("📁 Files in this Knowledge Base")

        filenames, file_types_summary = fetch_vector_store_filenames_and_types(selected_store.id)

        if not filenames:
            st.caption("No files attached to this knowledge base.")
        else:
            for name in filenames:
                st.markdown(f"- {name}")
        
        # Initialize or update assistant when vector store changes
        if st.session_state.selected_vector_store != selected_store.id:
            st.session_state.selected_vector_store = selected_store.id
            
            # Delete old assistant if exists
            if st.session_state.assistant_id:
                try:
                    client.beta.assistants.delete(st.session_state.assistant_id)
                except Exception:
                    pass
            
            # Create new assistant and thread
            with st.spinner("Initializing assistant..."):
                st.session_state.assistant_id = create_assistant(
                    selected_store.id, 
                    selected_store.name,
                    file_types_summary=file_types_summary,
                )
                reset_chat_session()
            
            st.success("✅ Assistant ready!")
        
    else:
        st.warning("⚠️ No vector stores found. Please create a vector store first.")
    
    st.divider()
    
    # Model info
    st.subheader("🤖 Model")
    st.info(f"**Active Model:** {model_chat}")
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        if st.session_state.thread_id:
            reset_chat_session()
        st.rerun()
    
    st.divider()
    
    # App info
    with st.expander("ℹ️ About", expanded=False):
        st.markdown("""
        **AI Knowledge Assistant**
        
        This app uses OpenAI's Assistants API with 
        Retrieval Augmented Generation (RAG) to provide 
        accurate answers based on your uploaded documents.
        
        **Features:**
        - 📚 Access to multiple knowledge bases
        - 🔍 Intelligent document search
        - 💬 Natural conversation interface
        - 📝 Source citations
        """)

# Main content
kb_id = st.session_state.get("selected_vector_store")

kb_files: list[str] = []
if kb_id:
    try:
        kb_files, _ = fetch_vector_store_filenames_and_types(kb_id)
    except Exception:
        kb_files = []

kb_files_line = ""
if kb_files:
    kb_files_line = "\n".join(f"- {name}" for name in kb_files)

if kb_files_line:
    st.markdown('<div class="kb-files-title">📚 Files in the selected knowledge base</div>', unsafe_allow_html=True)
    st.markdown(kb_files_line)

# Check if system is ready
if not vector_stores:
    st.error("❌ No vector stores available. Please create a vector store in your notebook first.")
    st.stop()

if not st.session_state.assistant_id or not st.session_state.thread_id:
    st.warning("⚠️ Initializing assistant... Please wait.")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# If a suggested question was clicked, process it like a normal chat prompt
if st.session_state.pending_prompt:
    pending = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    handle_user_prompt(pending)

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    handle_user_prompt(prompt)

# Welcome message if chat is empty
if len(st.session_state.messages) == 0:
    st.info("👋 Welcome! Ask me anything about your documents. I'll search through the knowledge base to provide accurate answers.")
    
    # Suggested questions
    st.subheader("💡 Suggested Questions")

    # Display suggested questions in a more compact way
    questions = [
        "📋 What topics are covered in the documents?",
        "🎯 What are the key learning objectives?",
        "📄 Can you provide a summary of the main document?",
        "🔑 What are the most important concepts?"
    ]

    cols = st.columns(2)
    for i, question in enumerate(questions):
        if cols[i % 2].button(question, use_container_width=True):
            st.session_state.pending_prompt = question
            st.rerun()

if st.session_state.user_role == "guest":
    guest_id = st.session_state.get("guest_id")
    if guest_id:
        today_str = date.today().isoformat()
        key = (guest_id, today_str)
        used = _guest_quota_by_id.get(key, 0)
        remaining = max(0, MAX_GUEST_QUERIES_PER_DAY - used)
        st.info(f"Guest mode ({guest_id}): {remaining} of {MAX_GUEST_QUERIES_PER_DAY} queries remaining today.")
    else:
        st.info("Guest mode: remaining daily queries depend on your guest ID.")
elif st.session_state.user_role == "admin":
    st.success("Admin mode: unlimited queries.")
