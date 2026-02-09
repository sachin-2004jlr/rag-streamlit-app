
import streamlit as st
import os
import shutil
import uuid
import io
import time
from docx import Document
from docx.shared import RGBColor # FIX: Import RGBColor
# Assuming the backend is in src/backend.py and class is AdvancedRAG
from src.backend import AdvancedRAG

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="RAG System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Backend
@st.cache_resource
def get_rag_engine():
    return AdvancedRAG()

rag_engine = get_rag_engine()

# ==========================================
# 2. SESSION STATE MANAGEMENT (PRIVACY & LOGIC)
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

# Define Paths based on Session ID (Data Isolation)
BASE_DIR = "temp_data"
USER_SESSION_DIR = os.path.join(BASE_DIR, st.session_state.session_id)
FILES_DIR = os.path.join(USER_SESSION_DIR, "files")
DB_DIR = os.path.join(USER_SESSION_DIR, "db")

# Ensure directories exist
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# Helper: Clean up session data
def cleanup_session_data():
    if os.path.exists(USER_SESSION_DIR):
        try:
            shutil.rmtree(USER_SESSION_DIR)
        except Exception as e:
            print(f"Error cleaning up: {e}")
    # Re-create for new session usage
    os.makedirs(FILES_DIR, exist_ok=True)
    os.makedirs(DB_DIR, exist_ok=True)

# Helper: Generate DOCX
def generate_document(messages):
    doc = Document()
    doc.add_heading('Conversation Log', 0)
    for msg in messages:
        role = "User" if msg["role"] == "user" else "AI"
        p = doc.add_paragraph()
        run = p.add_run(f"{role}: ")
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0) # FIX: Use RGBColor object
        doc.add_paragraph(msg["content"])
        doc.add_paragraph("-" * 20)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Model Map
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
    st.header("Chat Settings")
    
    # NEW CHAT
    if st.button("New Chat", type="primary", use_container_width=True):
        # Archive
        if st.session_state.messages:
            title = st.session_state.messages[0]['content'][:30] + "..."
            st.session_state.chat_history.insert(0, {
                "id": st.session_state.session_id,
                "title": title,
                "timestamp": time.strftime("%Y-%m-%d %H:%M")
            })
            
        # Cleanup
        cleanup_session_data()
        
        # Reset
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.db_ready = False
        st.rerun()

    st.divider()
    
    st.subheader("Chat History")
    if not st.session_state.chat_history:
        st.caption("No history yet.")
    for chat in st.session_state.chat_history:
        st.text(f"• {chat['title']}")

    st.divider()
    st.caption(f"Session: {st.session_state.session_id[:8]}...")

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("Multi Model RAG")
st.caption("Enterprise Intelligence System")

# LANDING PAGE (Setup)
if not st.session_state.db_ready:
    st.subheader("1. Select Model")
    model_friendly = st.selectbox(
        "Choose LLM:", 
        options=list(MODEL_MAP.keys()),
        index=0
    )
    st.session_state.current_model = MODEL_MAP[model_friendly]

    st.subheader("2. Upload Documents")
    # Using key=...session_id ensures uploader resets on new chat
    uploaded_files = st.file_uploader(
        "Upload PDF or DOCX", 
        accept_multiple_files=True,
        type=['pdf', 'docx', 'txt'],
        key=f"uploader_{st.session_state.session_id}" 
    )

    if uploaded_files:
        if st.button("Process Documents"):
            with st.spinner("Processing..."):
                # Save
                for file in uploaded_files:
                    with open(os.path.join(FILES_DIR, file.name), "wb") as f:
                        f.write(file.getbuffer())
                
                # Index
                status = rag_engine.process_documents(FILES_DIR, DB_DIR)
                
                if status == "Success":
                    st.session_state.db_ready = True
                    st.rerun()
                else:
                    st.error(f"Error: {status}")

# CHAT INTERFACE
else:
    # Top Bar: Model Info & Download
    col1, col2 = st.columns([4, 1])
    with col1:
        st.info(f"Chatting with **{st.session_state.current_model}**")
    with col2:
        if st.session_state.messages:
            docx = generate_document(st.session_state.messages)
            st.download_button("Download Log", docx, f"chat_log.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    # Chat Messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # AI Response
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = rag_engine.query(
                        query_text=st.session_state.messages[-1]["content"],
                        db_path=DB_DIR,
                        model_name=st.session_state.current_model
                    )
                    
                    # Handle response type
                    final_text = response
                    if isinstance(response, dict) and "answer" in response:
                        final_text = response["answer"]

                    st.write(final_text)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_text
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")