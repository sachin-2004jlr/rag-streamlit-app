
import streamlit as st
import os
import shutil
import uuid
import io
import time
from docx import Document
from docx.shared import RGBColor 
from src.backend import AdvancedRAG

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="RAG System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "No Emojis" and "Dark Black" Look
st.markdown("""
<style>
    /* Force Simple Black Background */
    .stApp {
        background-color: #000000;
        color: #e0e0e0;
    }
    
    /* Remove default Streamlit padding/margin around titles if needed */
    .block-container {
        padding-top: 2rem;
    }

    /* Simple Chat Message Styling (Without Emojis/Avatars) */
    .chat-msg {
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .chat-msg.user {
        background-color: #1a1a1a;
        border-left: 3px solid #3b82f6;
    }
    .chat-msg.ai {
        background-color: #0d0d0d;
        border-left: 3px solid #a855f7;
    }
    .chat-role {
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 0.9em;
        color: #888;
        text-transform: uppercase;
    }
    .chat-content {
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Backend
@st.cache_resource
def get_rag_engine():
    return AdvancedRAG()

rag_engine = get_rag_engine()

# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "db_ready" not in st.session_state:
    st.session_state.db_ready = False

if "current_model" not in st.session_state:
    st.session_state.current_model = "Llama 3.3 70B (Versatile)"

# Define Paths
BASE_DIR = "temp_data"
USER_SESSION_DIR = os.path.join(BASE_DIR, st.session_state.session_id)
FILES_DIR = os.path.join(USER_SESSION_DIR, "files")
DB_DIR = os.path.join(USER_SESSION_DIR, "db")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

def cleanup_session_data():
    if os.path.exists(USER_SESSION_DIR):
        try:
            shutil.rmtree(USER_SESSION_DIR)
        except Exception as e:
            print(f"Error cleaning up: {e}")
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)

def generate_document(messages):
    doc = Document()
    doc.add_heading('Conversation Log', 0)
    for msg in messages:
        role = "User" if msg["role"] == "user" else "AI"
        p = doc.add_paragraph()
        run = p.add_run(f"{role}: ")
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        doc.add_paragraph(msg["content"])
        doc.add_paragraph("-" * 20)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

MODEL_MAP = {
    "Llama 3.3 70B (Versatile)": "llama-3.3-70b-versatile",
    "Llama 3.1 8B (Instant)": "llama-3.1-8b-instant",
    "Llama 4 (Scout 17B)": "meta-llama/llama-4-scout-17b-16e-instruct",
    "Qwen 3 32B": "qwen/qwen3-32b",
    "GPT-OSS 20B": "openai/gpt-oss-20b"
}

# ==========================================
# 3. SIDEBAR
# ==========================================
with st.sidebar:
    st.header("Settings")
    
    if st.button("New Chat", type="primary", use_container_width=True):
        if st.session_state.messages:
            title = st.session_state.messages[0]['content'][:30] + "..."
            st.session_state.chat_history.insert(0, {
                "id": st.session_state.session_id,
                "title": title,
                "timestamp": time.strftime("%Y-%m-%d %H:%M")
            })
            
        cleanup_session_data()
        
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.db_ready = False
        st.rerun()

    st.divider()
    st.subheader("History")
    for chat in st.session_state.chat_history:
        st.text(f"• {chat['title']}")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("Multi Model RAG")
st.caption("Enterprise Intelligence System")

# LANDING PAGE
if not st.session_state.db_ready:
    st.subheader("1. Select Model")
    model_friendly = st.selectbox("Model", list(MODEL_MAP.keys()))
    st.session_state.current_model = MODEL_MAP[model_friendly]

    st.subheader("2. Upload Documents")
    uploaded_files = st.file_uploader("Upload Files", accept_multiple_files=True, key=f"uploader_{st.session_state.session_id}")

    if uploaded_files:
        if st.button("Process Documents"):
            with st.spinner("Processing..."):
                for file in uploaded_files:
                    with open(os.path.join(FILES_DIR, file.name), "wb") as f:
                        f.write(file.getbuffer())
                
                status = rag_engine.process_documents(FILES_DIR, DB_DIR)
                if status == "Success":
                    st.session_state.db_ready = True
                    st.rerun()
                else:
                    st.error(f"Error: {status}")

# CHAT INTERFACE
else:
    # Header
    c1, c2 = st.columns([5, 1])
    with c1:
        st.info(f"Model: {st.session_state.current_model}")
    with c2:
        if st.session_state.messages:
            docx = generate_document(st.session_state.messages)
            st.download_button("Download", docx, "log.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    # Messages (NO EMOJIS - pure Markdown text blocks)
    for msg in st.session_state.messages:
        role_label = "USER" if msg["role"] == "user" else "AI RESPONSE"
        css_class = "user" if msg["role"] == "user" else "ai"
        
        # HTML Injection for clean look without emojis
        st.markdown(f"""
        <div class="chat-msg {css_class}">
            <div class="chat-role">{role_label}</div>
            <div class="chat-content">{msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # AI Response logic
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        # Placeholder for AI "Thinking..."
        with st.spinner("Generating response..."):
            try:
                response = rag_engine.query(
                    query_text=st.session_state.messages[-1]["content"],
                    db_path=DB_DIR,
                    model_name=st.session_state.current_model
                )
                final_text = response["answer"] if isinstance(response, dict) else str(response)

                st.session_state.messages.append({"role": "assistant", "content": final_text})
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")