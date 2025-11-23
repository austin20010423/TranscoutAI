import streamlit as st
import llm_response
import time
import graphviz

# ---------------------------------------------------------------------
# Page Configuration & Custom CSS
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="Transcout AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a premium, modern tech look
st.markdown("""
<style>
    /* Main background and text colors are handled by Streamlit's theme, 
       but we can refine specific elements. */
    
    .stApp {
        background-color: #0E1117;
    }
    
    /* Chat message containers */
    .stChatMessage {
        background-color: #262730;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border: 1px solid #41444C;
    }
    
    /* User message specific style (if needed, though Streamlit handles this well) */
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1A1C24;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #FAFAFA;
    }
    
    /* Custom card for sources */
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
# Visualization Helper
# ---------------------------------------------------------------------
def visualize_sidebar(placeholder, sources):
    with placeholder.container():
        if not sources:
            st.info("No data to visualize yet. Ask a question!")
            return

        st.markdown("### 📊 Retrieval Analytics")
        
        # Knowledge Graph Visualization
        st.markdown("**Knowledge Graph**")
        try:
            graph = graphviz.Digraph()
            graph.attr(rankdir='LR', size='8,5', bgcolor='#1A1C24')
            graph.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#41444C')
            graph.attr('edge', color='#A0A0A0')

            for i, s in enumerate(sources):
                # Ticket Node
                ticket_id = f"t_{i}"
                label = s.get('title', 'Ticket')[:20] + "..."
                graph.node(ticket_id, label=label, fillcolor='#4A90E2', fontcolor='white')

                # Tags
                for tag in s.get("tags", []):
                    tag_id = f"tag_{tag}"
                    graph.node(tag_id, label=tag, shape='ellipse', fillcolor='#333', fontsize='10')
                    graph.edge(ticket_id, tag_id, label="HAS_TAG", fontsize='8')

                # Relationships
                for rel in s.get("relationships", []):
                    target_name = rel['node_props'].get('name', 'Unknown')
                    target_id = f"rel_{target_name}_{i}"
                    graph.node(target_id, label=target_name, shape='ellipse', fillcolor='#333', fontsize='10')
                    graph.edge(ticket_id, target_id, label=rel['relationship'], fontsize='8')

            st.graphviz_chart(graph)
        except Exception as e:
            st.error(f"Graph viz failed: {e}")


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.title("🚀 Transcout AI")
    st.markdown("---")
    
    # Placeholder for visualization
    viz_placeholder = st.empty()
    
    st.markdown("---")
    st.markdown("### About")
    st.info(
        "Transcout AI uses Graph RAG to retrieve the latest tech information "
        "and insights from a Neo4j knowledge graph."
    )
    
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------
# Main Chat Interface
# ---------------------------------------------------------------------

st.title("Transcout AI Assistant")
st.caption("Ask about the latest tech trends, startups, and tickets.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Find last sources to visualize initially
last_sources = []
for msg in reversed(st.session_state.messages):
    if msg.get("sources"):
        last_sources = msg["sources"]
        break
visualize_sidebar(viz_placeholder, last_sources)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 View Retrieved Sources"):
                for source in message["sources"]:
                    # Create a nice card for each source
                    tags_html = "".join([f'<span class="tag-badge">{tag}</span>' for tag in source.get('tags', [])])
                    
                    # Extract abstract from relationships
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

# Accept user input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Analyzing knowledge graph..."):
            try:
                # Call the backend
                response_data = llm_response.generate_response(prompt)
                answer = response_data["answer"]
                sources = response_data["sources"]
                
                # Simulate stream effect (optional, but nice)
                message_placeholder.markdown(answer)
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
                
                # Update Visualization Sidebar immediately
                visualize_sidebar(viz_placeholder, sources)
                
                # Display sources immediately for this turn
                if sources:
                    with st.expander("📚 View Retrieved Sources", expanded=True):
                        for source in sources:
                            tags_html = "".join([f'<span class="tag-badge">{tag}</span>' for tag in source.get('tags', [])])
                            
                            # Extract abstract from relationships
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
