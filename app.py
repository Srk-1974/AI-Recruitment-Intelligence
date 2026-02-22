import streamlit as st
import pandas as pd
import json
import os
import requests
import datetime
from datetime import datetime
from core.parser import extract_text
from core.analyzer import HRAnalyzer
from core.models import AnalysisRequest, ChatRequest

# Check if running on Streamlit Cloud
IS_CLOUD = "STREAMLIT_RUNTIME_ENV" in os.environ or "ST_CLOUD_APP" in os.environ

# Page Config
st.set_page_config(page_title="Intelligent HR Assistant", layout="wide", page_icon="☀️", initial_sidebar_state="expanded")

# Version: 1.7.5-PRO - Ultra Premium UI (Sync: 2026-02-22)
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
def get_analyzer(version):
    return HRAnalyzer()

analyzer = get_analyzer("1.7.5-PRO")

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
        <div style="text-align: center; margin: 80px auto 40px;">
            <div style="
                background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
                padding: 40px 60px;
                border-radius: 32px;
                box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
                display: inline-block;
                border: 1px solid rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            ">
                <div style="position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);"></div>
                <div style="display: flex; align-items: center; justify-content: center; gap: 30px; position: relative; z-index: 1;">
                    <div style="
                        background: linear-gradient(135deg, #6366f1, #a855f7);
                        padding: 20px;
                        border-radius: 20px;
                        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <span style="font-size: 56px;">☀️</span>
                    </div>
                    <div style="text-align: left;">
                        <h1 style="
                            margin: 0;
                            font-size: 42px;
                            font-weight: 900;
                            color: #ffffff;
                            letter-spacing: -1.5px;
                            line-height: 1;
                            text-transform: uppercase;
                        ">BHADRADRI</h1>
                        <p style="
                            margin: 4px 0 0 0;
                            font-size: 14px;
                            color: rgba(255, 255, 255, 0.7);
                            letter-spacing: 2px;
                            font-weight: 600;
                            text-transform: uppercase;
                        ">Technologies Inc | Intelligence Pro</p>
                    </div>
                </div>
            </div>
            <h2 style="margin-top: 25px; font-size: 24px; font-weight: 800; color: #1e1b4b; letter-spacing: -0.5px;">Enterprise Access Gateway</h2>
            <p style="opacity: 0.6; font-size: 13px; color: #64748b; font-weight: 500; margin-top: -5px;">Authorized Personnel Only</p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        cols = st.columns([1.5, 1, 1.5])
        with cols[1]:
            st.markdown("""
                <div style="padding: 10px 15px; text-align: center; background: #facc15; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 5px 15px rgba(250, 204, 21, 0.2);">
                    <p style="color: #1e1b4b; font-size: 0.75rem; margin-bottom: 8px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Secure Authentication Required</p>
            """, unsafe_allow_html=True)
            
            password = st.text_input("Access Key", type="password", placeholder="Enter key", label_visibility="collapsed")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🚀 Login", use_container_width=True):
                    if password == PRODUCTION_PASSWORD:
                        st.session_state["password_correct"] = True
                        st.rerun()
                    else:
                        st.session_state["password_incorrect"] = True
            with c2:
                if st.button("✖️ Reset", use_container_width=True):
                    st.session_state["password_incorrect"] = False
                    st.rerun()

            if st.session_state.get("password_incorrect", False):
                st.markdown('<p style="color: #ef4444; text-align: center; margin-top: 15px; font-weight: 600; font-size: 0.8rem;">🚫 Invalid Security Key.</p>', unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
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
        background: radial-gradient(circle at 0% 0%, #f1f5f9 0%, transparent 50%),
                    radial-gradient(circle at 100% 0%, #e0e7ff 0%, transparent 50%),
                    radial-gradient(circle at 100% 100%, #f5f3ff 0%, transparent 50%),
                    radial-gradient(circle at 0% 100%, #eff6ff 0%, transparent 50%),
                    #f8fafc;
        background-attachment: fixed;
    }

    /* Glassmorphism Card Style */
    .glass-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(25px) saturate(180%);
        -webkit-backdrop-filter: blur(25px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 28px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 
            0 20px 40px -15px rgba(0, 0, 0, 0.05),
            inset 0 0 0 1px rgba(255, 255, 255, 0.4);
        transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-8px) scale(1.01);
        background: rgba(255, 255, 255, 0.85);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 
            0 30px 60px -12px rgba(99, 102, 241, 0.08),
            inset 0 0 0 1px rgba(255, 255, 255, 0.6);
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 3.2rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #1e1b4b 0%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -2.5px;
        line-height: 1;
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
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 32px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.3) !important;
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

    /* Premium Deep Glass Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        padding: 8px;
        border-radius: 30px;
        margin-bottom: 40px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.4);
        overflow-x: auto;
        width: fit-content;
        max-width: 100%;
    }

    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
        display: none; /* Hide scrollbar for clean look */
    }

    .stTabs [data-baseweb="tab"] {
        height: 54px;
        border-radius: 25px !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 20px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        color: var(--text-muted) !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif;
        font-size: 1.05rem !important;
        letter-spacing: 0.3px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: var(--primary) !important;
        background: rgba(99, 102, 241, 0.05) !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
        transform: translateY(-2px);
    }
    
    /* Remove the default Streamlit underline for tabs */
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
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

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #f1f5f9;
    }
    </style>
    """, unsafe_allow_html=True)

# Handle Authentication
if not check_password():
    st.stop()

# Sidebar Branding with Logo
with st.sidebar:
    st.markdown("""
        <div style="margin-bottom: 12px;">
            <div style="
                background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
                padding: 6px 10px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 3px 10px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="
                        background: linear-gradient(135deg, #6366f1, #a855f7);
                        width: 28px;
                        height: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 6px;
                        flex-shrink: 0;
                    ">
                        <span style="font-size: 16px;">☀️</span>
                    </div>
                    <div style="overflow: hidden; line-height: 1.1;">
                        <p style="margin: 0; font-size: 12px; font-weight: 800; color: white; letter-spacing: -0.2px; text-transform: uppercase; white-space: nowrap;">BHADRADRI Technologies Inc</p>
                        <p style="margin: 1px 0 0 0; font-size: 7px; color: rgba(255, 255, 255, 0.5); letter-spacing: 0.8px; text-transform: uppercase; font-weight: 600; white-space: nowrap;">Intelligence Pro</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🛡️ HR Core v1.7.5-PRO")
    st.caption("🟢 Neural Network Active")
    st.caption("🔄 Last Updated: Feb 22, 2026")
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

# --- Safety Check: Provider/Model Compatibility Fix ---
# Ensures Sarvam AI doesn't crash with HTTP 400 if an old model is cached
if st.session_state.current_provider == "Sarvam AI":
    valid_sarvam_models = ["sarvam-m", "sarvam-30b", "sarvam-105b"]
    if st.session_state.current_model not in valid_sarvam_models:
        st.session_state.current_model = "sarvam-m" # Reset to safe default

if "current_temp" not in st.session_state:
    st.session_state.current_temp = 0.1
if "current_max_tokens" not in st.session_state:
    st.session_state.current_max_tokens = st.session_state.api_config.get("last_max_tokens", 3000)

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
tabs = st.tabs(["📄 Evaluation", "👥 Batch Ranking", "📜 History Vault", "💬 Expert AI", "⚙️ Admin"])

with tabs[0]:
    st.markdown('<h2 class="tab-subheader">📄 Single Resume Evaluation</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("#### 📝 Job Requirements")
            jd_input = st.text_area("JD Content", height=300, placeholder="Paste the Job Description here...", label_visibility="collapsed")
        with col2:
            st.markdown("#### 📤 Candidate Resume")
            resume_file = st.file_uploader("Upload PDF/DOCX", type=["pdf", "docx"], label_visibility="collapsed")
        
        if st.button("🚀 Start AI Analysis", use_container_width=True):
            if not jd_input or not resume_file:
                st.error("Please provide both Job Description and Resume.")
            else:
                with st.spinner(f"✨ AI ({provider}) is deep-scanning candidate profile..."):
                    try:
                        resume_text = extract_text(resume_file.name, resume_file.getvalue())
                        result = analyzer.analyze(
                            resume_text, jd_input, 
                            model_name=selected_model, temperature=temp_val, max_tokens=top_p_val,
                            provider=provider_key, api_key=api_key_val, ollama_url=ollama_url, azure_config=azure_config
                        )
                        st.session_state.current_analysis = result
                        st.session_state.eval_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "candidate_name": resume_file.name,
                            "match_percentage": result.match_percentage,
                            "ranking": result.ranking,
                            "result": result
                        })
                        if result.match_percentage >= 70:
                            st.balloons()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    if "current_analysis" in st.session_state:
        result = st.session_state.current_analysis
        st.markdown("---")
        st.markdown("### 📊 Analysis Insights")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="glass-card" style="text-align:center; border-top: 4px solid #6366f1;"><p style="color:var(--text-muted); font-weight:600; margin-bottom:0;">Match Score</p><h1>{result.match_percentage}%</h1></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="glass-card" style="text-align:center; border-top: 4px solid #8b5cf6;"><p style="color:var(--text-muted); font-weight:600; margin-bottom:0;">Fit Status</p><h1>{result.ranking}</h1></div>', unsafe_allow_html=True)
        with m3:
            # Simple count of matched skills
            st.markdown(f'<div class="glass-card" style="text-align:center; border-top: 4px solid #10b981;"><p style="color:var(--text-muted); font-weight:600; margin-bottom:0;">Skills Found</p><h1>{len(result.matched_skills)}</h1></div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Executive Summary")
        st.write(result.candidate_summary)
        st.markdown('</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="glass-card" style="height:100%">', unsafe_allow_html=True)
            st.markdown("#### ✅ Matched Skills")
            skills_html = "".join([f'<span class="skill-tag">{s}</span>' for s in result.matched_skills])
            st.markdown(skills_html or "_No direct skill matches detected._", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="glass-card" style="height:100%">', unsafe_allow_html=True)
            st.markdown("#### ❌ Missing Skills")
            missing_html = "".join([f'<span class="skill-tag missing-tag">{s}</span>' for s in result.missing_skills])
            st.markdown(missing_html or "_No critical missing skills detected._", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ⏳ Experience Evaluation")
        st.write(result.experience_evaluation)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="glass-card" style="border: 1px solid rgba(250, 204, 21, 0.3); background: linear-gradient(135deg, rgba(255,255,255,0.7) 0%, rgba(250, 204, 21, 0.05) 100%);">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                <div style="background: #facc15; padding: 10px; border-radius: 12px; box-shadow: 0 4px 12px rgba(250, 204, 21, 0.3);">
                    <span style="font-size: 20px;">🔍</span>
                </div>
                <h4 style="margin: 0; font-weight: 800; color: #854d0e; letter-spacing: -0.5px;">AI Matching Methodology & Scorecard</h4>
            </div>
            <div style="font-family: 'Inter', sans-serif;">
                {getattr(result, 'matching_explanation', 'Detailed scoring logic not available for this model.')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### ❓ Recommended Interview Questions")
        for q in result.interview_questions:
            st.markdown(f'<div style="padding:10px; background:#f8fafc; border-radius:10px; margin-bottom:8px; border-left:3px solid #6366f1;">🔹 {q}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<h2 class="tab-subheader">👥 Batch Candidate Ranking</h2>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        batch_jd = st.text_area("Job Description for Batch Ranking", height=200, key="batch_jd", placeholder="Define the criteria for this batch scan...")
        batch_resumes = st.file_uploader("Drop Multiple Resumes Here", type=["pdf", "docx"], accept_multiple_files=True)
        
        if st.button("🔥 Run Competitive Ranking", use_container_width=True):
            if not batch_jd or not batch_resumes:
                st.error("Please provide JD and at least one resume.")
            else:
                results = []
                progress_container = st.empty()
                for i, res in enumerate(batch_resumes):
                    try:
                        progress_container.markdown(f"🔄 Processing {i+1}/{len(batch_resumes)}: **{res.name}**")
                        resume_text = extract_text(res.name, res.getvalue())
                        result = analyzer.analyze(
                            resume_text, batch_jd, 
                            model_name=selected_model, temperature=temp_val, max_tokens=top_p_val,
                            provider=provider_key, api_key=api_key_val, ollama_url=ollama_url
                        )
                        from datetime import datetime
                        st.session_state.eval_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "candidate_name": res.name,
                            "match_percentage": result.match_percentage,
                            "ranking": getattr(result, 'ranking', 'N/A'),
                            "result": result
                        })
                        results.append({
                            "Candidate": res.name,
                            "Score": result.match_percentage,
                            "Status": result.ranking,
                            "Summary": result.candidate_summary
                        })
                    except Exception as e:
                        st.warning(f"Skipped {res.name}: {e}")
                
                if results:
                    st.markdown("---")
                    st.markdown("### 🏆 Final Batch Rankings")
                    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
                    
                    col_chart, col_table = st.columns([1, 2])
                    with col_chart:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.markdown("#### 📈 Score Distribution")
                        st.bar_chart(df.set_index('Candidate')['Score'])
                        st.markdown('</div>', unsafe_allow_html=True)
                    with col_table:
                        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                        st.markdown("#### 📋 Detailed Leaderboard")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tabs[2]:
    st.markdown('<h2 class="tab-subheader">📜 Evaluation Vault</h2>', unsafe_allow_html=True)
    
    if not st.session_state.eval_history:
        st.info("The vault is currently empty. Analyzed resumes will appear here.")
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        history_df = pd.DataFrame([
            {
                "ID": i,
                "Timestamp": item.get("timestamp"),
                "Candidate": item.get("candidate_name"),
                "Score": f"{item.get('match_percentage')}%",
                "Status": item.get("ranking")
            } for i, item in enumerate(st.session_state.eval_history)
        ])
        
        st.dataframe(history_df, use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns([3, 1])
        with c1:
            selected_id = st.selectbox("Select a profile to decrypt details", 
                                      options=range(len(st.session_state.eval_history)),
                                      format_func=lambda x: f"{st.session_state.eval_history[x]['candidate_name']} ({st.session_state.eval_history[x]['timestamp']})")
        with c2:
            st.write("") # Spacer
            if st.button("🔍 Open Profile", use_container_width=True):
                st.session_state.viewing_history_item = st.session_state.eval_history[selected_id]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.viewing_history_item:
        item = st.session_state.viewing_history_item
        res = item["result"]
        st.markdown("---")
        st.markdown(f'<h2 style="color:var(--primary)">🧐 Deep-Dive: {item["candidate_name"]}</h2>', unsafe_allow_html=True)
        st.caption(f"Analysis Registry Date: {item['timestamp']}")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="glass-card" style="text-align:center;"><h4>Match Score</h4><h2>{res.match_percentage}%</h2></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="glass-card" style="text-align:center;"><h4>Rank</h4><h2>{res.ranking}</h2></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="glass-card" style="text-align:center;"><h4>Skills</h4><h2>{len(res.matched_skills)}</h2></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("#### 🖋️ AI Summary")
        st.write(res.candidate_summary)
        st.markdown('</div>', unsafe_allow_html=True)
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown('<div class="glass-card" style="height:100%">', unsafe_allow_html=True)
            st.success("Matched Competencies")
            st.write(", ".join(res.matched_skills))
            st.markdown('</div>', unsafe_allow_html=True)
        with col_s2:
            st.markdown('<div class="glass-card" style="height:100%">', unsafe_allow_html=True)
            st.error("Missing Requirements")
            st.write(", ".join(res.missing_skills))
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown('<div class="glass-card" style="border-left: 5px solid #6366f1;">', unsafe_allow_html=True)
        st.markdown("#### 💡 Historical Matching Scorecard")
        st.markdown(getattr(res, 'matching_explanation', 'Detailed scoring logic not available for this legacy record.'))
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🏃 Close Vault Profile", use_container_width=True):
            st.session_state.viewing_history_item = None
            st.rerun()

with tabs[3]:
    st.markdown('<h2 class="tab-subheader">☀️ Recruitment Expert AI</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="glass-card" style="margin-bottom:10px;">', unsafe_allow_html=True)
    st.info("👋 Hello! I am your Recruitment Intelligence expert. Ask me about candidate trends, JD optimization, or app features.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat Container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            role_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
            avatar = "👤" if message["role"] == "user" else "☀️"
            st.markdown(f"""
                <div style="display:flex; flex-direction:column; gap:4px; margin-bottom:15px;">
                    <div style="font-size:0.7rem; color:var(--text-muted); align-self:{'flex-end' if message['role'] == 'user' else 'flex-start'}; margin-bottom:2px;">
                        {avatar} {message['role'].upper()}
                    </div>
                    <div class="chat-bubble {role_class}">
                        {message["content"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # React to user input
    if prompt := st.chat_input("Message the HR Brain..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # Rerun to show user message immediately

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Expert is typing..."):
            try:
                assistant_response = analyzer.chat(
                    st.session_state.messages[-1]["content"], 
                    st.session_state.messages[:-1],
                    model_name=selected_model, temperature=temp_val, max_tokens=top_p_val,
                    provider=provider_key, api_key=api_key_val, ollama_url=ollama_url, azure_config=azure_config
                )
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                st.rerun()
            except Exception as e:
                st.error(f"Brain connection failed: {e}")

    if st.button("🗑️ Reset Brain Conversation", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

with tabs[4]:
    st.markdown('<h2 class="tab-subheader">🛠️ System Control & Core Settings</h2>', unsafe_allow_html=True)
    
    # 1. Admin Password Security
    if "settings_unlocked" not in st.session_state:
        st.session_state.settings_unlocked = False
    
    ADMIN_PASSWORD = "admin123" 
    
    if not st.session_state.settings_unlocked:
        st.markdown('<div class="glass-card" style="text-align:center; padding: 50px 20px;">', unsafe_allow_html=True)
        st.markdown("### 🔐 Security Wall")
        st.markdown("Technical engine settings are encrypted and locked.")
        admin_pass = st.text_input("Enter Admin Access Key", type="password", key="main_admin_pass", label_visibility="collapsed")
        if st.button("🔓 Authenticate & Unlock", use_container_width=True):
            if admin_pass == ADMIN_PASSWORD:
                st.session_state.settings_unlocked = True
                st.success("Identity Verified!")
                st.rerun()
            else:
                st.error("Access Denied: Incorrect Password")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Unlock logic
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col_header, col_lock = st.columns([4, 1])
        with col_header:
            st.markdown("### ☀️ Model & Engine Grid")
        with col_lock:
            if st.button("🔒 Revoke Access", use_container_width=True):
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
            available_models = ["sarvam-m", "sarvam-30b", "sarvam-105b"]
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
        
        # Token Limit Slider
        new_tokens = st.slider("Max Token Response Limit", 100, 6000, st.session_state.current_max_tokens, 100)
        if new_tokens != st.session_state.current_max_tokens:
            st.session_state.current_max_tokens = new_tokens
            st.session_state.api_config["last_max_tokens"] = new_tokens
            save_config(st.session_state.api_config)
            st.rerun()

        st.markdown("---")
        st.caption("Advanced system tools are available in the sidebar.")

# Copyright Footer
st.markdown("""
    <div style="text-align: center; margin-top: 80px; padding: 40px 20px; border-top: 1px solid #f1f5f9;">
        <p style="font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 4px;">© 2026 Bhadradri Technologies Inc.</p>
        <p style="font-size: 11px; color: #64748b; letter-spacing: 1px; text-transform: uppercase;">Enterprise Recruitment Intelligence | v1.7.5-PRO</p>
    </div>
""", unsafe_allow_html=True)
