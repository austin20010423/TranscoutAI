import streamlit as st
import llm_response
from datetime import datetime

# ---------------------------------------------------------------------
# Page Configuration & Custom CSS
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Transcout AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS matching the reference UI
st.markdown("""
<style>
    .stApp {
        background-color: #000000;
    }

    .main .block-container {
        background-color: #000000;
        padding-top: 2rem;
        padding-bottom: 100px;
    }

    section[data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #1E1E1E;
        min-height: 100vh;
        position: relative;
        padding: 24px 20px 120px 20px;
    }

    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        border: none;
        color: #9CA3AF;
        text-align: left;
        padding: 10px 12px;
        font-weight: 400;
        box-shadow: none;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #2A2A2A;
        color: #FFFFFF;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .logo-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
        padding: 10px 0;
    }

    .logo-text {
        font-size: 1.5rem;
        font-weight: 600;
        color: #FFFFFF;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .sidebar-divider {
        height: 1px;
        width: 100%;
        background: linear-gradient(90deg, rgba(255,255,255,0), rgba(107,114,128,0.4), rgba(255,255,255,0));
        margin: 18px 0;
    }

    button[key="new_chat"] {
        background-color: #DC2626 !important;
        color: white !important;
        border: none !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        padding: 12px 16px !important;
        text-align: center !important;
    }

    button[key="new_chat"]:hover {
        background-color: #B91C1C !important;
    }

    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
    }

    .rocket-emoji {
        font-size: 5rem;
        margin-bottom: 20px;
    }

    .welcome-text {
        color: #FFFFFF;
        font-size: 1.5rem;
        font-weight: 400;
        margin-bottom: 40px;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stButton > button {
        background-color: #1F1F1F;
        border: 1px solid #333333;
        border-radius: 10px;
        padding: 20px;
        color: #FFFFFF;
        font-size: 0.95rem;
        font-weight: 400;
        width: 100%;
        text-align: left;
        transition: all 0.2s;
        box-shadow: none;
    }

    .stButton > button:hover {
        background-color: #2A2A2A;
        border-color: #444444;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }

    .stButton > button:focus-visible {
        outline: 2px solid #8B5CF6;
        outline-offset: 2px;
    }

    .stChatInputContainer {
        position: fixed;
        bottom: 20px;
        left: 0;
        right: 0;
        padding: 0 20px;
        background-color: #000000;
    }

    .stChatInput > div > div {
        background: rgba(20, 20, 20, 0.75);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.45);
        backdrop-filter: blur(12px);
    }

    .stChatInput input {
        color: #FFFFFF;
    }

    .stChatInput input::placeholder {
        color: #6B7280;
    }

    .stChatMessage {
        background-color: transparent;
        padding: 10px 0;
    }

    h1, h2, h3 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #FAFAFA;
    }

    .source-card {
        background-color: #1E212B;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        transition: transform 0.2s;
    }

    .source-card:hover {
        transform: translateY(-2px);
        border-color: #4A90E2;
    }

    .source-title {
        font-weight: bold;
        color: #4A90E2;
        font-size: 1.1em;
    }

    .source-meta {
        font-size: 0.85em;
        color: #A0A0A0;
        margin-top: 5px;
    }

    .tag-badge {
        background-color: #333;
        color: #EEE;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        margin-right: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Session State & Suggestions
# ---------------------------------------------------------------------
SUGGESTION_PROMPTS = [
    {"icon": "🛰️", "text": "Which startups are building AI products in Texas?"},
    {"icon": "🌉", "text": "Startups based in San Francisco, California"},
    {"icon": "🎬", "text": "Startup related to content creation"},
    {"icon": "🤖", "text": "Artificial Intelligence startups"},
]

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


def render_suggestion_buttons(show_heading: bool = False, key_prefix: str = "main"):
    """Display the quick-start suggestion buttons in a 2x2 grid."""
    container = st.container()
    if show_heading:
        container.markdown("### Quick suggestions")
    col1, col2 = container.columns(2, gap="large")
    cols = [col1, col2]
    for idx, suggestion in enumerate(SUGGESTION_PROMPTS):
        with cols[idx % 2]:
            if st.button(
                f"{suggestion['icon']} {suggestion['text']}",
                key=f"{key_prefix}_suggestion_{idx}",
                use_container_width=True,
            ):
                st.session_state.pending_prompt = suggestion["text"]
                st.rerun()

# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div class="logo-container">
        <span style="font-size: 1.8rem;">🚀</span>
        <span class="logo-text">Transcout AI</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

    if st.button("+ New chat", key="new_chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_session_id = None
        st.rerun()
    
    st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
    
    if st.session_state.chat_sessions:
        for i, session in enumerate(st.session_state.chat_sessions[-3:]):
            session_title = session.get("title", f"Chat {i+1}")
            if st.button(session_title, key=f"chat_{i}", use_container_width=True):
                st.session_state.current_session_id = session.get("id")
                st.rerun()
    else:
        st.markdown("""
        <div style="color:#6B7280;font-size:0.9rem;padding:16px 0;">
            <div style="height:1px;background:#333;margin:15px 0;"></div>
            <div style="height:1px;background:#333;margin:15px 0;"></div>
            <div style="height:1px;background:#333;margin:15px 0;"></div>
        </div>
        """, unsafe_allow_html=True)
    

# ---------------------------------------------------------------------
# Main Chat Interface
# ---------------------------------------------------------------------

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-container">
        <div class="rocket-emoji">🚀</div>
        <div class="welcome-text">How can I help you?</div>
    </div>
    """, unsafe_allow_html=True)
    render_suggestion_buttons(show_heading=False, key_prefix="welcome")
else:
    render_suggestion_buttons(show_heading=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Retrieved Sources"):
                for source in message["sources"]:
                    tags_html = "".join([f'<span class="tag-badge">{tag}</span>' for tag in source.get('tags', [])])
                    abstract = "No abstract available."
                    for rel in source.get('relationships', []):
                        if rel.get('node_type') == 'content' and 'text' in rel.get('node_props', {}):
                            abstract = rel['node_props']['text']
                            break
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-title">{source.get('title', 'Untitled')}</div>
                        <div class="source-meta">
                            <strong>Type:</strong> {source.get('type', 'N/A')} | 
                            <strong>Similarity:</strong> {source.get('similarity', 0)}
                        </div>
                        <div style="margin-top:8px; font-size:0.9em; color:#CCC;">
                            {abstract}
                        </div>
                        <div style="margin-top:8px;">{tags_html}</div>
                    </div>
                    """, unsafe_allow_html=True)

prompt = None
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
else:
    prompt = st.chat_input("Message Transcout AI")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    if not st.session_state.current_session_id:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.current_session_id = session_id
        st.session_state.chat_sessions.append({
            "id": session_id,
            "title": prompt[:30] + "..." if len(prompt) > 30 else prompt,
            "created_at": datetime.now()
        })
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.spinner("Analyzing knowledge graph..."):
            try:
                response_data = llm_response.generate_response(prompt)
                answer = response_data["answer"]
                sources = response_data["sources"]
                message_placeholder.markdown(answer)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
                
                if sources:
                    with st.expander("📚 View Retrieved Sources", expanded=True):
                        for source in sources:
                            tags_html = "".join([f'<span class="tag-badge">{tag}</span>' for tag in source.get('tags', [])])
                            abstract = "No abstract available."
                            for rel in source.get('relationships', []):
                                if rel.get('node_type') == 'content' and 'text' in rel.get('node_props', {}):
                                    abstract = rel['node_props']['text']
                                    break
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-title">{source.get('title', 'Untitled')}</div>
                                <div class="source-meta">
                                    <strong>Type:</strong> {source.get('type', 'N/A')} | 
                                    <strong>Similarity:</strong> {source.get('similarity', 0)}
                                </div>
                                <div style="margin-top:8px; font-size:0.9em; color:#CCC;">
                                    {abstract}
                                </div>
                                <div style="margin-top:8px;">{tags_html}</div>
                            </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"An error occurred: {e}")
