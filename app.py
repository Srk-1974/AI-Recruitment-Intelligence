import streamlit as st
import pandas as pd
import json
import os
import requests
from core.parser import extract_text
from core.analyzer import HRAnalyzer
from core.models import AnalysisRequest, ChatRequest

# Check if running on Streamlit Cloud
IS_CLOUD = "STREAMLIT_RUNTIME_ENV" in os.environ or "ST_CLOUD_APP" in os.environ

# Page Config
st.set_page_config(page_title="Intelligent HR Assistant", layout="wide", page_icon="☀️", initial_sidebar_state="expanded")

# Version: 1.7.3 - Default Model Fix (Sync: 2026-02-18)
# Initialize Session States
if "eval_history" not in st.session_state:
    st.session_state.eval_history = []
if "viewing_history_item" not in st.session_state:
    st.session_state.viewing_history_item = None

# Configuration Management
CONFIG_FILE = "api_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# Load config into session state if not present
if "api_config" not in st.session_state:
    st.session_state.api_config = load_config()

# Initialize Analyzer Early
@st.cache_resource(ttl=3600)
def get_analyzer():
    return HRAnalyzer()

analyzer = get_analyzer()

# Simple Authentication Logic
def check_password():
    """Returns True if the user had the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    # Use Streamlit Secrets for production, fallback to srk123 for local
    # Use Streamlit Secrets for production, fallback to srk123 for local
    PRODUCTION_PASSWORD = "srk123"
    if IS_CLOUD:
        try:
            PRODUCTION_PASSWORD = st.secrets.get("PASSWORD", "srk123")
        except Exception:
            pass # Keep default

    # Logo and Header for Login Page
    st.markdown("""
        <div style="text-align: center; margin: 40px auto 20px;">
            <div style="
                background: linear-gradient(135deg, #4f46e5, #818cf8);
                padding: 30px 40px;
                border-radius: 24px;
                box-shadow: 0 20px 40px rgba(79, 70, 229, 0.15);
                display: inline-block;
                border: 1px solid rgba(255, 255, 255, 0.1);
            ">
                <div style="display: flex; align-items: center; justify-content: center; gap: 24px;">
                    <div style="
                        background: rgba(255, 255, 255, 0.2);
                        padding: 15px;
                        border-radius: 16px;
                        backdrop-filter: blur(10px);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <span style="font-size: 48px;">☀️</span>
                    </div>
                    <div style="text-align: left;">
                        <h1 style="
                            margin: 0;
                            font-size: 42px;
                            font-weight: 800;
                            color: #ffffff;
                            letter-spacing: -1px;
                            line-height: 1;
                        ">BHADRADRI</h1>
                        <p style="
                            margin: 4px 0 0 0;
                            font-size: 14px;
                            color: rgba(255, 255, 255, 0.8);
                            letter-spacing: 4px;
                            font-weight: 500;
                            text-transform: uppercase;
                        ">Technology Inc.</p>
                    </div>
                </div>
            </div>
            <h2 style="margin-top: 30px; font-size: 28px; font-weight: 700; color: #1e293b; letter-spacing: -0.5px;">Recruitment Intelligence Pro</h2>
            <p style="opacity: 0.5; font-size: 14px; color: #64748b;">Enterprise Grade AI Orchestration</p>
        </div>
        <div style="max-width: 450px; margin: 0 auto 30px; text-align: center;">
             <div style="background: white; padding: 20px; border-radius: 16px; border: 1px solid #f1f5f9; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
                <span style="color: #64748b; font-size: 0.9rem;">Please sign in to access your dashboard</span>
             </div>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        cols = st.columns([1, 2, 1])
        with cols[1]:
            password = st.text_input("Password", type="password", label_visibility="collapsed")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🚀 Login", use_container_width=True):
                    if password == PRODUCTION_PASSWORD:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        st.session_state["password_incorrect"] = True
            with c2:
                if st.button("✖️ Cancel", use_container_width=True):
                    st.session_state["password"] = ""
                    st.rerun()

            if st.session_state.get("password_incorrect", False):
                st.markdown('<p style="color: #ef4444; text-align: center; margin-top: 10px;">❌ Wrong password! Please try again.</p>', unsafe_allow_html=True)
    
    return False

# --- Custom CSS for Premium Enterprise Look ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #8b5cf6;
        --accent: #facc15;
        --bg-main: #f8fafc;
        --sidebar-bg: #0f172a;
        --card-bg: rgba(255, 255, 255, 0.8);
        --text-main: #1e293b;
        --text-muted: #64748b;
        --glass-border: rgba(99, 102, 241, 0.1);
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main {
        background-color: var(--bg-main);
        background-image: radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.05) 0px, transparent 50%),
                          radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
    }

    /* Glassmorphism Card Style */
    .glass-card {
        background: var(--card-bg);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.1), 0 10px 10px -5px rgba(99, 102, 241, 0.04);
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #4f46e5, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stCaption {
        color: rgba(255, 255, 255, 0.8) !important;
    }

    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        text-transform: none;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2);
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
        color: white;
    }
    
    .stButton>button:active {
        transform: scale(0.98);
    }

    /* Sidebar Specific Buttons */
    [data-testid="stSidebar"] .stButton>button {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        backdrop-filter: blur(5px);
    }
    
    [data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: var(--primary) !important;
    }

    /* Input Fields */
    .stTextArea textarea, .stTextInput input {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: rgba(255, 255, 255, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    /* Pill Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: white;
        padding: 8px 12px;
        border-radius: 16px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
    }

    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 12px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 24px !important;
        transition: all 0.3s ease !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
        font-family: 'Outfit', sans-serif;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-main) !important;
        color: var(--primary) !important;
        font-weight: 700 !important;
    }

    /* Chat Bubbles */
    .chat-bubble {
        padding: 16px 20px;
        border-radius: 18px;
        margin-bottom: 12px;
        max-width: 85%;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .user-bubble {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
    
    .assistant-bubble {
        background: white;
        color: var(--text-main);
        border: 1px solid #f1f5f9;
        border-bottom-left-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }

    /* Skill Tags */
    .skill-tag {
        display: inline-flex;
        align-items: center;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 30px;
        background: rgba(99, 102, 241, 0.08);
        color: var(--primary-dark);
        border: 1px solid rgba(99, 102, 241, 0.1);
        font-size: 0.85rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .skill-tag:hover {
        background: rgba(99, 102, 241, 0.15);
        transform: scale(1.05);
    }
    
    .missing-tag {
        background: rgba(ef, 44, 44, 0.08);
        color: #dc2626;
        border-color: rgba(220, 38, 38, 0.1);
    }

    /* Subheader with modern underline */
    .tab-subheader {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text-main);
        margin-bottom: 24px;
        letter-spacing: -0.5px;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* File Uploader Customization */
    [data-testid="stFileUploader"] {
        background-color: white;
        padding: 20px;
        border-radius: 16px;
        border: 2px dashed #e2e8f0;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary);
        background-color: var(--bg-main);
    }
    </style>
    """, unsafe_allow_html=True)

# Handle Authentication
if not check_password():
    st.stop()

# Sidebar Branding with Logo
with st.sidebar:
    st.markdown("""
        <div style="margin-bottom: 25px;">
            <div style="
                background: linear-gradient(135deg, #4f46e5, #6366f1);
                padding: 12px 16px;
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="
                        background: rgba(255, 255, 255, 0.2);
                        padding: 8px;
                        border-radius: 8px;
                    ">
                        <span style="font-size: 18px;">☀️</span>
                    </div>
                    <div style="text-align: left;">
                        <p style="margin: 0; font-size: 14px; font-weight: 700; color: white; letter-spacing: -0.5px;">BHADRADRI</p>
                        <p style="margin: 0; font-size: 8px; color: rgba(255, 255, 255, 0.7); letter-spacing: 1.5px; text-transform: uppercase;">Portal Pro</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🛡️ HR Intelligence v1.7.3")
    st.caption("🟢 Production Mode Active")
    st.caption("🔄 Last Sync: Feb 18, 12:45 EST")
    if st.button("🚪 Logout"):
        # Clear all session state to force a full reset to defaults upon next login
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    # Note about Engine Settings
    st.markdown("---")
    st.info("⚙️ **Engine Settings** have moved to the **Settings** tab.")
    
    st.markdown("### 🚑 System Tools")
    if st.button("🧼 Clear Cache", use_container_width=True):
        st.cache_resource.clear()
        st.toast("Cache Cleared!")
    
    if st.button("🔥 Health Check", use_container_width=True):
        st.info(f"Connected to: {st.session_state.current_provider}")

# Initialize Engine Variables at top level (accessible to all tabs)
# Use session state to persist choices
if "current_provider" not in st.session_state:
    st.session_state.current_provider = st.session_state.api_config.get("last_provider", "Groq")
if "current_model" not in st.session_state:
    st.session_state.current_model = st.session_state.api_config.get("last_model", "llama-3.3-70b-versatile")
if "current_temp" not in st.session_state:
    st.session_state.current_temp = 0.1
if "current_max_tokens" not in st.session_state:
    st.session_state.current_max_tokens = 2000

# Set local variables based on session state/config
provider = st.session_state.current_provider
selected_model = st.session_state.current_model
temp_val = st.session_state.current_temp
top_p_val = st.session_state.current_max_tokens
ollama_url = "http://localhost:11434" # Default
api_key_val = None
azure_config = None
provider_key = "Ollama"

# Map provider display name to key
provider_map = {
    "Ollama (Local PC)": "Ollama",
    "Groq": "Groq",
    "OpenAI": "OpenAI",
    "Sarvam AI": "SarvamAI",
    "DeepSeek": "DeepSeek",
    "Gemini": "Gemini",
    "Azure OpenAI (Copilot)": "AzureOpenAI"
}
provider_key = provider_map.get(provider, "Ollama")

# Load existing keys/configs for active provider
if provider_key == "AzureOpenAI":
    azure_config = {
        "endpoint": st.session_state.api_config.get("azure_endpoint", ""),
        "api_key": st.session_state.api_config.get("azure_key", ""),
        "deployment_name": st.session_state.api_config.get("azure_deployment", ""),
        "api_version": st.session_state.api_config.get("azure_version", "2024-02-15-preview")
    }
else:
    api_key_val = st.session_state.api_config.get(provider_key)

st.markdown(' <h1 style="font-size: 3rem; font-weight: 800; margin-bottom: 0;">AI Recruitment <span style="color: #6366f1;">Intelligence</span></h1>', unsafe_allow_html=True)
st.markdown('<p style="font-size: 1.2rem; color: #64748b; margin-top: -10px;">Enterprise Candidate Ranking & Assessment Engine</p>', unsafe_allow_html=True)
st.markdown('<div style="height: 2px; background: linear-gradient(90deg, #6366f1 0%, transparent 100%); margin: 20px 0 40px 0;"></div>', unsafe_allow_html=True)

# Tabs Configuration
tabs = st.tabs(["📄 Single Evaluation", "👥 Batch Ranking", "📜 Analysis History", "💬 Recruitment ChatBot", "⚙️ Admin Settings"])

with tabs[0]:
    st.markdown('<h2 class="tab-subheader">📄 Single Resume Evaluation</h2>', unsafe_allow_html=True)
    st.write("")
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        jd_input = st.text_area("Job Description", height=300, placeholder="Paste the Job Description here...")
    
    with col2:
        resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
    
    if st.button("Analyze Resume"):
        if not jd_input or not resume_file:
            st.error("Please provide both Job Description and Resume.")
        else:
            with st.spinner(f"AI ({provider}) is analyzing..."):
                try:
                    # Direct call instead of requests.post
                    resume_text = extract_text(resume_file.name, resume_file.getvalue())
                    result = analyzer.analyze(
                        resume_text, 
                        jd_input, 
                        model_name=selected_model,
                        temperature=temp_val,
                        max_tokens=top_p_val,
                        provider=provider_key,
                        api_key=api_key_val,
                        ollama_url=ollama_url,
                        azure_config=azure_config
                    )
                    
                    st.success("Analysis Complete!")
                    
                    # Save to History
                    from datetime import datetime
                    history_item = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "candidate_name": resume_file.name,
                        "match_percentage": result.match_percentage,
                        "ranking": result.ranking,
                        "result": result
                    }
                    st.session_state.eval_history.append(history_item)
                    
                    # Set the current result for display below
                    st.session_state.current_analysis = result
                    
                    # Dashboard Metrics
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid #7c3aed;">
                            <p style="margin:0; opacity:0.7; font-weight:600;">Match Confidence</p>
                            <h1 style="margin:0; font-size: 3rem; color: #7c3aed;">{result.match_percentage}%</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid #38bdf8;">
                            <p style="margin:0; opacity:0.7; font-weight:600;">Recommended Rank</p>
                            <h1 style="margin:0; font-size: 3rem; color: #0284c7;">{result.ranking}</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"""
                        <div class="glass-card" style="border-top: 4px solid #10b981;">
                            <p style="margin:0; opacity:0.7; font-weight:600;">Skills Match</p>
                            <h1 style="margin:0; font-size: 3rem; color: #059669;">{len(result.matched_skills)}</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("### 📝 Executive Summary")
                    st.markdown(f"""
                    <div class="glass-card">
                        {result.candidate_summary}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### 🛠 Skill Analysis")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.subheader("✅ Matched Competencies")
                        skills_html = "".join([f'<span class="skill-tag">{s}</span>' for s in result.matched_skills])
                        st.markdown(skills_html, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with c2:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.subheader("❌ Missing Requirements")
                        missing_html = "".join([f'<span class="skill-tag missing-tag">{s}</span>' for s in result.missing_skills])
                        st.markdown(missing_html, unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    st.markdown("### 📊 Experience Evaluation")
                    st.markdown(f"""
                    <div class="glass-card">
                        {result.experience_evaluation}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("### ❓ AI-Generated Interview Questions")
                    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                    questions = getattr(result, 'interview_questions', [])
                    if questions:
                        for q in questions:
                            st.markdown(f"🔹 **{q}**")
                    else:
                        st.info("No interview questions generated.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    err_msg = str(e)
                    st.error(f"Analysis failed: {err_msg}")
                    if "insufficient_quota" in err_msg:
                        st.warning("⚠️ **OpenAI Quota Exceeded** on this batch item.")
                        st.info("💡 **Tip**: Switch to **Ollama** in the sidebar to run large batches for free without quota limits!")
                    st.info("💡 **Tip**: If using a local LLM, make sure the model is pulled and your laptop isn't sleeping.")

with tabs[1]:
    st.markdown('<h2 class="tab-subheader">👥 Batch Candidate Ranking</h2>', unsafe_allow_html=True)
    st.write("")
    batch_jd = st.text_area("Job Description for Ranking", height=200, key="batch_jd", placeholder="What are you looking for in this candidates batch?")
    batch_resumes = st.file_uploader("Upload Multiple Resumes", type=["pdf", "docx"], accept_multiple_files=True)
    
    if st.button("Rank All Candidates"):
        if not batch_jd or not batch_resumes:
            st.error("Please provide JD and at least one resume.")
        else:
            results = []
            progress_bar = st.progress(0)
            for i, res in enumerate(batch_resumes):
                try:
                    resume_text = extract_text(res.name, res.getvalue())
                    result = analyzer.analyze(
                        resume_text, 
                        batch_jd, 
                        model_name=selected_model,
                        temperature=temp_val,
                        max_tokens=top_p_val,
                        provider=provider_key,
                        api_key=api_key_val,
                        ollama_url=ollama_url
                    )
                    
                    # Save each batch item to history
                    from datetime import datetime
                    st.session_state.eval_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "candidate_name": res.name,
                        "match_percentage": result.match_percentage,
                        "ranking": getattr(result, 'ranking', 'N/A'),
                        "result": result
                    })

                    results.append({
                        "candidate_name": res.name,
                        "match_percentage": result.match_percentage,
                        "ranking": result.ranking,
                        "candidate_summary": result.candidate_summary # Changed to result.candidate_summary
                    })
                except Exception as e:
                    st.warning(f"Could not process {res.name}: {e}")
                progress_bar.progress((i + 1) / len(batch_resumes))
            
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.subheader("📊 Ranking Analytics")
                df = pd.DataFrame(results)
                # Sort by score
                df = df.sort_values(by="match_percentage", ascending=False)
                st.dataframe(df[['candidate_name', 'match_percentage', 'ranking', 'candidate_summary']], use_container_width=True)
                st.bar_chart(df.set_index('candidate_name')['match_percentage'])
                st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<h2 class="tab-subheader">📜 Evaluation History</h2>', unsafe_allow_html=True)
    st.write("")
    st.markdown("---")
    
    if not st.session_state.eval_history:
        st.info("No evaluations found in this session. Start by analyzing a resume!")
    else:
        # Create a display dataframe
        history_df = pd.DataFrame([
            {
                "ID": i,
                "Time": item.get("timestamp", "N/A"),
                "Candidate": item.get("candidate_name", "Unknown"),
                "Score": f"{item.get('match_percentage', 0)}%",
                "Rank": item.get("ranking", "N/A")
            } for i, item in enumerate(st.session_state.eval_history)
        ])
        
        st.dataframe(history_df.set_index("ID"), use_container_width=True)
        
        # Details Selection
        selected_id = st.selectbox("Select an evaluation to view details", 
                                  options=range(len(st.session_state.eval_history)),
                                  format_func=lambda x: f"{st.session_state.eval_history[x]['candidate_name']} ({st.session_state.eval_history[x]['timestamp']})")
        
        if st.button("🔍 View Details"):
            st.session_state.viewing_history_item = st.session_state.eval_history[selected_id]
            st.rerun()

    # Show detailed view if selected
    if st.session_state.viewing_history_item:
        item = st.session_state.viewing_history_item
        res = item["result"]
        st.markdown("---")
        st.markdown(f"## 🧐 Details: {item['candidate_name']}")
        st.caption(f"Analyzed on {item['timestamp']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Match Score", f"{res.match_percentage}%")
        with col2:
            st.metric("Ranking", res.ranking)
        with col3:
            st.metric("Skills Found", len(res.matched_skills))
        
        st.markdown("### 📝 Summary")
        st.write(res.candidate_summary)
        
        st.markdown("### 🛠 Skills")
        c1, c2 = st.columns(2)
        with c1:
            st.success("Matched Skills")
            st.write(", ".join(res.matched_skills))
        with c2:
            st.error("Missing Skills")
            st.write(", ".join(res.missing_skills))
            
        st.markdown("### ❓ Interview Questions")
        for q in res.interview_questions:
            st.markdown(f"🔹 {q}")

        if st.button("🏃 Close Details"):
            st.session_state.viewing_history_item = None
            st.rerun()

with tabs[3]:
    st.markdown('<h2 class="tab-subheader">☀️ Recruitment ChatBot</h2>', unsafe_allow_html=True)
    st.write("")
    st.markdown("---")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        role_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
        st.markdown(f"""
            <div class="chat-bubble {role_class}">
                {message["content"]}
            </div>
        """, unsafe_allow_html=True)

    # React to user input
    if prompt := st.chat_input("Ask me anything about the app or recruitment..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("AI is thinking..."):
            try:
                assistant_response = analyzer.chat(
                    prompt, 
                    st.session_state.messages[:-1],
                    model_name=selected_model,
                    temperature=temp_val,
                    max_tokens=top_p_val,
                    provider=provider_key,
                    api_key=api_key_val,
                    ollama_url=ollama_url,
                    azure_config=azure_config
                )
                
                # Display assistant response
                st.markdown(f"""
                    <div class="chat-bubble assistant-bubble">
                        {assistant_response}
                    </div>
                """, unsafe_allow_html=True)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            except Exception as e:
                st.error(f"Chat failed: {e}")

    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

with tabs[4]:
    st.markdown('<h2 class="tab-subheader">🛡️ Intelligence Control Center</h2>', unsafe_allow_html=True)
    st.write("")
    st.markdown("""
        <div class="glass-card" style="padding: 15px; border-left: 5px solid #a78bfa; margin-bottom: 20px;">
            <h4 style="margin:0;">⚙️ Engine Configuration</h4>
            <p style="margin:5px 0 0 0; font-size: 0.9rem; opacity: 0.8;">
                Manage AI providers, API keys, and model parameters securely.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Admin Password Security
    if "settings_unlocked" not in st.session_state:
        st.session_state.settings_unlocked = False
    
    ADMIN_PASSWORD = "admin123" 
    
    if not st.session_state.settings_unlocked:
        st.warning("🔒 Technical settings are locked for unauthorized users.")
        c1, c2 = st.columns([3, 1])
        with c1:
            admin_pass = st.text_input("Enter Admin Password to Unlock Settings", type="password", key="main_admin_pass")
        with c2:
            st.write("") # Spacing
            st.write("")
            if st.button("🔓 Unlock Settings", use_container_width=True):
                if admin_pass == ADMIN_PASSWORD:
                    st.session_state.settings_unlocked = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Invalid Administrative Password")
    else:
        # Unlock logic
        col_header, col_lock = st.columns([4, 1])
        with col_lock:
            if st.button("🔒 Lock Settings", use_container_width=True):
                st.session_state.settings_unlocked = False
                st.rerun()
        
        # --- Actual Settings UI (Locked behind password) ---
        st.markdown('### ☀️ Model & Provider Selection', unsafe_allow_html=True)
        # Initialize some vars
        available_models = ["llama3.2"]

        # 1. Radio for Provider
        new_provider = st.radio(
            "Active AI Provider", 
            ["Ollama (Local PC)", "Groq", "OpenAI", "Sarvam AI", "DeepSeek", "Gemini", "Azure OpenAI (Copilot)"], 
            index=["Ollama (Local PC)", "Groq", "OpenAI", "Sarvam AI", "DeepSeek", "Gemini", "Azure OpenAI (Copilot)"].index(st.session_state.current_provider),
            horizontal=True
        )
        if new_provider != st.session_state.current_provider:
            st.session_state.current_provider = new_provider
            st.session_state.api_config["last_provider"] = new_provider
            save_config(st.session_state.api_config)
            st.rerun()

        # Helper for API Key UI
        def render_api_key_ui_main(provider_name, label):
            current_key = st.session_state.api_config.get(provider_name, "")
            input_key = f"main_{provider_name}_input"
            if input_key not in st.session_state:
                st.session_state[input_key] = current_key
            visibility_key = f"main_{provider_name}_show"
            if visibility_key not in st.session_state:
                st.session_state[visibility_key] = False
            input_type = "default" if st.session_state[visibility_key] else "password"
            user_input = st.text_input(label, type=input_type, key=input_key, placeholder="Enter API Key")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💾 Save Key", key=f"msave_{provider_name}", use_container_width=True):
                    st.session_state.api_config[provider_name] = user_input
                    save_config(st.session_state.api_config)
                    st.toast("Key Saved!")
                    st.rerun()
            with c2:
                if st.button("🗑️ Delete", key=f"mdel_{provider_name}", use_container_width=True):
                    if provider_name in st.session_state.api_config:
                        del st.session_state.api_config[provider_name]
                        save_config(st.session_state.api_config)
                        del st.session_state[input_key]
                        st.rerun()
            with c3:
                blabel = "🙈 Hide" if st.session_state[visibility_key] else "👁️ Show"
                if st.button(blabel, key=f"mshow_{provider_name}", use_container_width=True):
                    st.session_state[visibility_key] = not st.session_state[visibility_key]
                    st.rerun()
            return user_input

        # Logic for each provider display
        if st.session_state.current_provider == "Ollama (Local PC)":
            raw_url = st.text_input("Ollama Base URL", value="http://localhost:11434")
            ollama_url = raw_url.strip().rstrip('/')
            try:
                available_models = analyzer.get_available_models(custom_url=ollama_url)
            except:
                available_models = ["llama3.2"]
        
        elif st.session_state.current_provider == "Groq":
            available_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b"]
            render_api_key_ui_main("Groq", "Groq API Key")
        
        elif st.session_state.current_provider == "OpenAI":
            available_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
            render_api_key_ui_main("OpenAI", "OpenAI API Key")

        elif st.session_state.current_provider == "Sarvam AI":
            available_models = ["sarvam-2b-v0.5", "yoddha-2b", "openhathi-7b-hi-v0.1-base"]
            render_api_key_ui_main("SarvamAI", "Sarvam API Key")

        elif st.session_state.current_provider == "DeepSeek":
            available_models = ["deepseek-chat", "deepseek-reasoner"]
            render_api_key_ui_main("DeepSeek", "DeepSeek API Key")

        elif st.session_state.current_provider == "Gemini":
            available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
            render_api_key_ui_main("Gemini", "Gemini API Key")

        elif st.session_state.current_provider == "Azure OpenAI (Copilot)":
            st.markdown("#### Azure Connection Parameters")
            az_endpoint = st.session_state.api_config.get("azure_endpoint", "")
            az_key = st.session_state.api_config.get("azure_key", "")
            az_deployment = st.session_state.api_config.get("azure_deployment", "")
            az_version = st.session_state.api_config.get("azure_version", "2024-02-15-preview")
            c1, c2 = st.columns(2)
            with c1:
                ui_az_endpoint = st.text_input("Endpoint URL", value=az_endpoint)
                ui_az_deployment = st.text_input("Deployment Name", value=az_deployment)
            with c2:
                ui_az_key = st.text_input("API Key", value=az_key, type="password")
                ui_az_version = st.text_input("API Version", value=az_version)
            
            if st.button("💾 Save Azure Configuration", use_container_width=True):
                st.session_state.api_config.update({
                    "azure_endpoint": ui_az_endpoint,
                    "azure_key": ui_az_key,
                    "azure_deployment": ui_az_deployment,
                    "azure_version": ui_az_version
                })
                save_config(st.session_state.api_config)
                st.success("Azure Settings Updated!")
                st.rerun()
            available_models = [ui_az_deployment] if ui_az_deployment else ["Enter Deployment Name"]

        # 2. Model Selection
        new_model = st.selectbox(
            "Active AI Model", 
            available_models,
            index=available_models.index(st.session_state.current_model) if st.session_state.current_model in available_models else 0
        )
        if new_model != st.session_state.current_model:
            st.session_state.current_model = new_model
            st.session_state.api_config["last_model"] = new_model
            save_config(st.session_state.api_config)
            st.rerun()

        # 3. Parameters
        st.markdown("### ⚙️ Inference Parameters")
        new_tokens = st.slider("Max Token Response Limit", 100, 4000, st.session_state.current_max_tokens, 100)
        if new_tokens != st.session_state.current_max_tokens:
            st.session_state.current_max_tokens = new_tokens
            st.rerun()

        st.markdown("---")
        st.caption("Advanced system tools are available in the sidebar.")

# Copyright Footer
st.markdown("""
    <div style="text-align: center; margin-top: 80px; padding: 40px 20px; border-top: 1px solid #f1f5f9;">
        <p style="font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">© 2026 Bhadradri Technologies Inc.</p>
        <p style="font-size: 11px; color: #64748b; letter-spacing: 1px; text-transform: uppercase;">Enterprise Recruitment Intelligence | v1.7.3</p>
    </div>
""", unsafe_allow_html=True)
