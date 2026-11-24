import streamlit as st
import requests
import json
import time

# Page Configuration
st.set_page_config(
    page_title="Self-Healing RAG Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Injectable CSS with Glassmorphism, Modern Typography & Vibrant Animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Animated Hero Header */
    .hero-container {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(168, 85, 247, 0.08) 50%, rgba(236, 72, 153, 0.08) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.15);
        backdrop-filter: blur(10px);
        text-align: center;
    }

    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .hero-subtitle {
        color: #4B5563;
        font-size: 1.15rem;
        font-weight: 500;
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Stat Cards Header */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-label {
        color: #6B7280;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #111827;
        margin-top: 0.25rem;
    }

    /* Custom Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .badge-success {
        background: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
    }
    .badge-warning {
        background: #FFFBEB;
        color: #B45309;
        border: 1px solid #FDE68A;
    }
    .badge-danger {
        background: #FEF2F2;
        color: #B91C1C;
        border: 1px solid #FECACA;
    }

    /* Output Card */
    .output-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 5px solid #4F46E5;
        border-radius: 16px;
        padding: 1.75rem;
        margin: 1.5rem 0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        font-size: 1.1rem;
        line-height: 1.7;
        color: #1F2937;
    }

    /* Trace Timeline Steps */
    .timeline-container {
        margin-top: 1.5rem;
        position: relative;
        padding-left: 1rem;
    }
    
    .timeline-item {
        position: relative;
        padding: 1rem 1.25rem;
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        margin-bottom: 0.75rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
        color: #374151;
        transition: all 0.2s ease;
    }

    .timeline-item:hover {
        background: #FFFFFF;
        border-color: #C7D2FE;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.08);
    }

    .timeline-retrieve { border-left: 4px solid #3B82F6; }
    .timeline-generate { border-left: 4px solid #8B5CF6; }
    .timeline-critique-pass { border-left: 4px solid #10B981; }
    .timeline-critique-fail { border-left: 4px solid #F59E0B; }
    .timeline-reformulate { border-left: 4px solid #EC4899; }
    .timeline-fallback { border-left: 4px solid #EF4444; }

    /* Form & Input Adjustments */
    .stTextArea textarea {
        border-radius: 12px;
        border: 1.5px solid #E5E7EB;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1rem;
        transition: border-color 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: #4F46E5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }

    /* Submit Button styling */
    .stButton button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        font-weight: 700;
        font-size: 1.05rem;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        border: none;
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">⚡ Self-Healing RAG Engine</div>
    <div class="hero-subtitle">
        Stateful LangGraph agent featuring iterative LLM fact-checking, automatic search query reformulation, and fallback safety bounds.
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Pipeline Control Center")
api_url = st.sidebar.text_input("FastAPI Endpoint", value="http://localhost:8000/ask")
max_retries = st.sidebar.slider("Max Retries Cap", min_value=1, max_value=2, value=2, help="Enforced limit on reformulation loops.")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧪 Quick Presets")
preset = st.sidebar.radio(
    "Choose a scenario to test:",
    (
        "✨ Custom Question",
        "💰 Meal Expense Allowance (Answerable)",
        "💻 Technology Stipend (Answerable)",
        "⚡ Cloud Engine API Limits (Answerable)",
        "🔧 Troubleshooting ERR-401 (Answerable)",
        "🛡️ Parental Leave Policy (Triggers Fallback)"
    )
)

default_text = ""
if preset == "💰 Meal Expense Allowance (Answerable)":
    default_text = "What is the daily meal reimbursement limit during business travel?"
elif preset == "💻 Technology Stipend (Answerable)":
    default_text = "What is the equipment stipend for new hires at AcroCorp?"
elif preset == "⚡ Cloud Engine API Limits (Answerable)":
    default_text = "What are the API rate limits and timeouts for the Cloud Engine Pro tier?"
elif preset == "🔧 Troubleshooting ERR-401 (Answerable)":
    default_text = "How do I resolve error ERR-401 authentication token expired?"
elif preset == "🛡️ Parental Leave Policy (Triggers Fallback)":
    default_text = "What is AcroCorp's parental leave and maternity policy?"

# Main Form Input
with st.form(key="rag_interactive_form"):
    st.markdown("#### 💬 Ask a Question")
    question = st.text_area(
        "Enter query below:",
        value=default_text,
        placeholder="e.g. What is the equipment stipend for new hires?",
        height=110,
        label_visibility="collapsed"
    )
    
    col_submit, col_space = st.columns([2, 3])
    with col_submit:
        submit_btn = st.form_submit_button("🚀 Run Self-Healing Graph", use_container_width=True)

# Execution Handling
if submit_btn and question.strip():
    start_clk = time.time()
    with st.spinner("🔄 Executing graph: retrieve → generate → critique → [reformulate / finalize]..."):
        try:
            payload = {
                "question": question.strip(),
                "max_retries": max_retries
            }
            response = requests.post(api_url, json=payload, timeout=60)
            elapsed_sec = round(time.time() - start_clk, 2)
            
            if response.status_code == 200:
                data = response.json()
                final_response = data.get("final_response", "")
                grounded = data.get("grounded", False)
                retry_count = data.get("retry_count", 0)
                trace_log = data.get("trace_log", [])
                
                st.markdown("---")
                
                # Metrics Row
                m_col1, m_col2, m_col3 = st.columns(3)
                
                with m_col1:
                    if grounded and "don't have enough information" not in final_response.lower():
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Fact-Check Status</div>
                            <div style="margin-top:0.4rem;">
                                <span class="badge badge-success">Grounded ✅</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif grounded and "don't have enough information" in final_response.lower():
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Fact-Check Status</div>
                            <div style="margin-top:0.4rem;">
                                <span class="badge badge-warning">No Info in Context ℹ️</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="metric-card">
                            <div class="metric-label">Fact-Check Status</div>
                            <div style="margin-top:0.4rem;">
                                <span class="badge badge-danger">Fallback Triggered 🛑</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                with m_col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Reformulation Loops</div>
                        <div class="metric-value">{retry_count} / {max_retries} Retries</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with m_col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">Execution Latency</div>
                        <div class="metric-value">{elapsed_sec}s</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Final Output Card
                st.markdown("#### 🎯 Verified Output")
                st.markdown(f'<div class="output-card">{final_response}</div>', unsafe_allow_html=True)
                
                # Execution Trace Log Timeline
                st.markdown("#### 🔄 Self-Healing Execution Trace Timeline")
                with st.expander("🔍 Inspect Node Trajectory & Log History", expanded=True):
                    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
                    for step in trace_log:
                        # Styling classes based on node type
                        css_class = "timeline-item"
                        if "Retrieve" in step:
                            css_class += " timeline-retrieve"
                        elif "Generate" in step:
                            css_class += " timeline-generate"
                        elif "Passed fact-check" in step:
                            css_class += " timeline-critique-pass"
                        elif "Failed fact-check" in step:
                            css_class += " timeline-critique-fail"
                        elif "Reformulate" in step:
                            css_class += " timeline-reformulate"
                        elif "Fallback" in step:
                            css_class += " timeline-fallback"
                            
                        st.markdown(f'<div class="{css_class}">{step}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error(f"Backend API Error ({response.status_code}): {response.text}")
                
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Could not connect to FastAPI server. Ensure `uvicorn src.api:app --reload` is running on port 8000.")
        except Exception as e:
            st.error(f"Unexpected Exception: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#9CA3AF; font-size:0.85rem;">Powered by LangGraph • ChromaDB • OpenAI gpt-4o-mini • FastAPI</div>',
    unsafe_allow_html=True
)
