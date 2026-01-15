"""
Streamlit RAG Chat Application
Interactive chat interface with OpenAI vector stores
"""

import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .st-emotion-cache-1v0mbdj {
        border-radius: 10px;
    }
    h1 {
        color: #1e88e5;
        font-weight: 700;
    }
    .stAlert {
        border-radius: 10px;
    }
    .vector-store-info {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1e88e5;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Initialize and return OpenAI client"""
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = get_openai_client()

# Get model from env, with fallback for Assistants API compatibility
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
if env_model in SUPPORTED_ASSISTANT_MODELS:
    model_chat = env_model
else:
    # Fallback to gpt-4o-mini if the env model is not supported
    model_chat = "gpt-4o-mini"
    st.info(f"ℹ️ Model '{env_model}' is not supported by Assistants API. Using '{model_chat}' instead.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "selected_vector_store" not in st.session_state:
    st.session_state.selected_vector_store = None

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

# Create assistant
def create_assistant(vector_store_id, vector_store_name):
    """Create an OpenAI assistant with file search capability"""
    try:
        assistant = client.beta.assistants.create(
            name=f"Assistant for {vector_store_name}",
            instructions=f"""You are a knowledgeable AI assistant with access to documents in the '{vector_store_name}' knowledge base.
            
Your role is to:
- Provide accurate, detailed answers based on the documents in the knowledge base
- Cite specific sources when applicable
- Be clear when information is not available in the knowledge base
- Maintain a helpful, professional, and friendly tone
- Provide well-structured responses with proper formatting
- Be concise and to the point and brief 

Always prioritize accuracy and cite your sources when answering questions.""",
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

# Get assistant response
def get_assistant_response(thread_id, assistant_id, user_message):
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
            
            # Get the latest assistant message
            for message in messages.data:
                if message.role == "assistant":
                    for content in message.content:
                        if content.type == 'text':
                            return content.text.value
            
            return "I couldn't generate a response. Please try again."
        else:
            return f"Error: Run failed with status {run.status}"
            
    except Exception as e:
        return f"Error getting response: {str(e)}"

# Sidebar
with st.sidebar:
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
        
        # Display vector store info
        st.markdown(f"""
        <div class="vector-store-info">
            <strong>📊 Store Details</strong><br>
            <strong>Name:</strong> {selected_store.name}<br>
            <strong>Files:</strong> {selected_store.file_counts.total}<br>
            <strong>Status:</strong> {selected_store.status}
        </div>
        """, unsafe_allow_html=True)
        
        # Initialize or update assistant when vector store changes
        if st.session_state.selected_vector_store != selected_store.id:
            st.session_state.selected_vector_store = selected_store.id
            
            # Delete old assistant if exists
            if st.session_state.assistant_id:
                try:
                    client.beta.assistants.delete(st.session_state.assistant_id)
                except:
                    pass
            
            # Create new assistant
            with st.spinner("Initializing assistant..."):
                st.session_state.assistant_id = create_assistant(
                    selected_store.id, 
                    selected_store.name
                )
                
                # Create new thread
                st.session_state.thread_id = create_thread()
                
                # Clear chat history when switching stores
                st.session_state.messages = []
            
            st.success("✅ Assistant ready!")
        
    else:
        st.warning("⚠️ No vector stores found. Please create a vector store first.")
    
    st.divider()
    
    # Model info
    st.subheader("🤖 Model")
    if model_chat != env_model:
        st.info(f"**Active Model:** {model_chat}\n\n⚠️ Using fallback ('{env_model}' not supported)")
    else:
        st.info(f"**Active Model:** {model_chat}")
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.thread_id:
            st.session_state.thread_id = create_thread()
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
st.title("🤖 AI Knowledge Assistant")
st.markdown("Ask questions about your documents and get intelligent, context-aware responses.")

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

# Chat input
if prompt := st.chat_input("Ask me anything about your documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get assistant response
    with st.chat_message("assistant"):
        response = get_assistant_response(
            st.session_state.thread_id,
            st.session_state.assistant_id,
            prompt
        )
        st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Welcome message if chat is empty
if len(st.session_state.messages) == 0:
    st.info("👋 Welcome! Ask me anything about your documents. I'll search through the knowledge base to provide accurate answers.")
    
    # Suggested questions
    st.subheader("💡 Suggested Questions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 What topics are covered?", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("🎯 What are the learning objectives?", use_container_width=True):
            st.rerun()
