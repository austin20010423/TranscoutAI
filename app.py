import streamlit as st
import llm_response
import time

# Page Config
st.set_page_config(
    page_title="Transcout AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Gemini-like styling
st.markdown("""
<style>
    /* General Dark Theme adjustments */
    .stApp {
        background-color: #131314;
        color: #E3E3E3;
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        background-color: #1E1F20;
        color: #E3E3E3;
        border-radius: 24px;
        border: 1px solid #444746;
        padding: 12px 20px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #A8C7FA;
        box-shadow: none;
    }

    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: row;
        align-items: flex-start;
    }
    .chat-message.user {
        background-color: #1E1F20;
    }
    .chat-message.bot {
        background-color: transparent;
    }
    .chat-message .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 1rem;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 20px;
    }
    .chat-message.user .avatar {
        background-color: #8AB4F8;
        color: #131314;
    }
    .chat-message.bot .avatar {
        background-color: linear-gradient(135deg, #4285F4, #9B72CB); /* Gemini gradient approximation */
        color: white;
    }
    .chat-message .content {
        flex-grow: 1;
    }
    
    /* Source card styling */
    .source-card {
        background-color: #1E1F20;
        border: 1px solid #444746;
        border-radius: 12px;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .source-title {
        font-weight: bold;
        color: #A8C7FA;
        font-size: 1.1em;
    }
    .source-meta {
        font-size: 0.9em;
        color: #C4C7C5;
        margin-top: 5px;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Header
st.title("✨ Gemini Clone")
st.caption("Powered by Neo4j & OpenAI")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            with st.expander("📚 Sources"):
                for source in message["sources"]:
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-title">{source.get('title', 'Untitled')}</div>
                        <div class="source-meta">
                            Type: {source.get('type', 'Unknown')} | 
                            Tags: {', '.join(source.get('tags', []))}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# Accept user input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            try:
                # Call backend
                response_data = llm_response.generate_response(prompt)
                full_response = response_data["answer"]
                sources = response_data["sources"]
                
                # Simulate stream (optional, just for effect if backend isn't streaming)
                # For now, just display it.
                message_placeholder.markdown(full_response)
                
                # Display sources
                if sources:
                    with st.expander("📚 Sources", expanded=True):
                        for source in sources:
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-title">{source.get('title', 'Untitled')}</div>
                                <div class="source-meta">
                                    Type: {source.get('type', 'Unknown')} | 
                                    Tags: {', '.join(source.get('tags', []))}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                # Add assistant response to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "sources": sources
                })
                
            except Exception as e:
                st.error(f"An error occurred: {e}")

