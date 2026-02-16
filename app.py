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
st.set_page_config(page_title="Intelligent HR Assistant", layout="wide", page_icon="🤖")

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
        <div style="text-align: center; margin: 50px auto 30px;">
            <div style="
                background: linear-gradient(135deg, #1e3a8a, #059669);
                padding: 20px 50px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(30, 64, 175, 0.4);
                display: inline-block;
            ">
                <div style="display: flex; align-items: center; justify-content: center; gap: 20px;">
                    <div style="
                        background: rgba(255, 255, 255, 0.2);
                        padding: 12px;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <span style="font-size: 42px;">🏹</span>
                    </div>
                    <div style="text-align: left;">
                        <h1 style="
                            margin: 0;
                            font-size: 36px;
                            font-weight: 800;
                            color: #4ade80;
                            letter-spacing: 2px;
                            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                        ">BHADRADRI</h1>
                        <p style="
                            margin: 5px 0 0 0;
                            font-size: 13px;
                            color: rgba(255, 255, 255, 0.95);
                            letter-spacing: 4px;
                            font-weight: 300;
                        ">TECHNOLOGY INC.</p>
                    </div>
                </div>
            </div>
            <h2 style="margin-top: 25px; font-size: 24px; color: #38bdf8;">HR Intelligence Assistant</h2>
            <p style="opacity: 0.6; font-size: 14px;">© 2026 Bhadradri Technologies Inc. All Rights Reserved</p>
        </div>
        <div class="glass-card" style="max-width: 400px; margin: 30px auto;">
            <h2 style="text-align: center;">🔑 Recruitment Intelligence Portal</h2>
            <p style="text-align: center; opacity: 0.7;">Production Environment Secure Login</p>
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

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    .stApp {
        background: transparent;
    }

    /* Glassmorphism containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(74, 222, 128, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Custom Tags */
    .skill-tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 20px;
        background: rgba(34, 197, 94, 0.1);
        color: #4ade80;
        border: 1px solid rgba(74, 222, 128, 0.3);
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .missing-tag {
        background: rgba(239, 68, 68, 0.1);
        color: #f87171;
        border-color: rgba(248, 113, 113, 0.3);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #22c55e 0%, #10b981 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 700;
        letter-spacing: 0.5px;
        transition: transform 0.2s;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
    }

    /* Headers */
    h1 {
        background: linear-gradient(90deg, #4ade80, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    .sidebar .sidebar-content {
        background: #0f172a;
    }
    
    /* Hide Streamlit Branding and Menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# Handle Authentication
if not check_password():
    st.stop()

# Sidebar Branding with Logo
with st.sidebar:
    # Logo at top of sidebar
    st.markdown("""
        <div style="text-align: center; margin-bottom: 15px;">
            <div style="
                background: linear-gradient(135deg, #1e3a8a, #059669);
                padding: 8px 15px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(30, 64, 175, 0.3);
            ">
                <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <div style="
                        background: rgba(255, 255, 255, 0.15);
                        padding: 6px;
                        border-radius: 4px;
                    ">
                        <span style="font-size: 16px;">🏹</span>
                    </div>
                    <div style="text-align: left;">
                        <p style="
                            margin: 0;
                            font-size: 13px;
                            font-weight: 700;
                            color: #4ade80;
                            letter-spacing: 0.8px;
                        ">BHADRADRI</p>
                        <p style="
                            margin: 0;
                            font-size: 7px;
                            color: rgba(255, 255, 255, 0.9);
                            letter-spacing: 2px;
                        ">TECHNOLOGY INC.</p>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🛡️ HR Intelligence v1.7")
    st.caption("🟢 Production Mode Active")
    st.caption("🔄 Last Sync: Feb 4, 17:01 EST")
    if st.button("🚪 Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
    st.markdown("---")
    st.markdown("### ⚙️ Engine Settings")
    
    # Admin Password Protection for Engine Settings
    if "settings_unlocked" not in st.session_state:
        st.session_state.settings_unlocked = False
    
    ADMIN_PASSWORD = "admin123"  # Default admin password
    
    if not st.session_state.settings_unlocked:
        st.warning("🔒 Engine Settings are locked. Enter admin password to unlock.")
        col1, col2 = st.columns([3, 1])
        with col1:
            admin_pass = st.text_input("Admin Password", type="password", key="admin_password_input")
        with col2:
            if st.button("🔓 Unlock", use_container_width=True):
                if admin_pass == ADMIN_PASSWORD:
                    st.session_state.settings_unlocked = True
                    st.success("Settings unlocked!")
                    st.rerun()
                else:
                    st.error("Incorrect password!")
        st.stop()  # Stop rendering the rest of the settings
    
    # Lock button (when unlocked)
    if st.button("🔒 Lock Settings"):
        st.session_state.settings_unlocked = False
        st.rerun()
    
    provider = st.radio("AI Provider", ["Ollama (Local PC)", "Groq", "OpenAI", "Sarvam AI", "DeepSeek", "Gemini", "Azure OpenAI (Copilot)"], horizontal=True)
    
    # Initialize defaults
    ollama_url = "http://localhost:11434"
    api_key_val = None
    azure_config = None # Dictionary to hold Azure settings
    
    # Helper for API Key UI
    def render_api_key_ui(provider_name, label):
        # Load current key from config
        current_key = st.session_state.api_config.get(provider_name, "")
        
        # UI Layout: Input first, then buttons below
        # specific_key handles the input state
        input_key = f"{provider_name}_input"
        if input_key not in st.session_state:
            st.session_state[input_key] = current_key

        # Track visibility state for Show/Hide button
        visibility_key = f"{provider_name}_show"
        if visibility_key not in st.session_state:
            st.session_state[visibility_key] = False

        # Determine input type based on visibility state
        input_type = "default" if st.session_state[visibility_key] else "password"
        user_input = st.text_input(label, type=input_type, key=input_key, placeholder="Enter API Key")

        # Buttons in a separate row with three columns: Save, Delete, Show/Hide
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Save", key=f"save_{provider_name}", use_container_width=True):
                if user_input:
                    st.session_state.api_config[provider_name] = user_input
                    save_config(st.session_state.api_config)
                    st.toast(f"{provider_name} Key Saved!", icon="✅")
                    st.rerun()
                else:
                    st.warning("Enter a key to save.")

        with col2:
            if st.button("🗑️ Delete", key=f"del_{provider_name}", use_container_width=True):
                if provider_name in st.session_state.api_config:
                    del st.session_state.api_config[provider_name]
                    save_config(st.session_state.api_config)
                    # Clear session state input
                    del st.session_state[input_key]
                    st.toast(f"{provider_name} Key Deleted!", icon="🗑️")
                    st.rerun()
                else:
                    st.info("No key to delete.")

        with col3:
            # Show/Hide toggle button
            button_label = "🙈 Hide" if st.session_state[visibility_key] else "👁️ Show"
            if st.button(button_label, key=f"show_{provider_name}", use_container_width=True):
                st.session_state[visibility_key] = not st.session_state[visibility_key]
                st.rerun()
        
        # Return the content of the text input (current value), not just the saved config
        return user_input

    available_models = []
    provider_key = ""

    if provider == "Ollama (Local PC)":
        provider_key = "Ollama"
        raw_url = st.text_input("Local Ollama URL", value="http://localhost:11434", help="Use your Ngrok URL if connecting your laptop to this portal.")
        ollama_url = raw_url.strip().rstrip('/')
        
        if IS_CLOUD and "localhost" in ollama_url:
            st.warning("⚠️ **Localhost is not accessible from the Web.**")
            st.info("💡 **How to connect your laptop?** \n1. Run: `ngrok http 11434 --host-header=\"localhost:11434\"` \n2. Paste the `https://xxxx.ngrok-free.app` URL here.")
            
        # Dynamic Model Loading for Ollama
        try:
            available_models = analyzer.get_available_models(custom_url=ollama_url)
            if not available_models or available_models == ["llama3.2"]:
                st.caption("⚠️ Using default model list (Check connection)")
        except Exception as e:
            st.error(f"Ollama Error: {e}")
            available_models = ["llama3.2"]
    
    elif provider == "Groq":
        provider_key = "Groq"
        available_models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b"]
        st.caption("Groq API Key")
        api_key_val = render_api_key_ui("Groq", "Groq API Key")
    
    elif provider == "OpenAI":
        provider_key = "OpenAI"
        available_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        st.caption("OpenAI API Key")
        api_key_val = render_api_key_ui("OpenAI", "OpenAI API Key")

    elif provider == "Sarvam AI":
        provider_key = "SarvamAI"
        available_models = ["sarvam-2b-v0.5", "yoddha-2b", "openhathi-7b-hi-v0.1-base"] 
        st.caption("Sarvam AI API Key (Supports Indian languages)")
        api_key_val = render_api_key_ui("SarvamAI", "Sarvam API Key")

    elif provider == "DeepSeek":
        provider_key = "DeepSeek"
        available_models = ["deepseek-chat", "deepseek-reasoner"]
        st.caption("DeepSeek API Key")
        api_key_val = render_api_key_ui("DeepSeek", "DeepSeek API Key")
    
    elif provider == "Gemini":
        provider_key = "Gemini"
        available_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]
        st.caption("Google Gemini API Key")
        api_key_val = render_api_key_ui("Gemini", "Gemini API Key")

    elif provider == "Azure OpenAI (Copilot)":
        provider_key = "AzureOpenAI"
        available_models = ["gpt-4", "gpt-3.5-turbo"] # User defines deployment, these are just placeholders/hints if needed, but actually model name is deployment name usually. 
        # For Azure, model selection is often 'Deployment Name'. 
        # We can let user pick a dummy model or type it? 
        # Actually in Azure, the 'model_name' param usually maps to deployment name in LangChain if not specified otherwise.
        # But `AzureChatOpenAI` takes `azure_deployment`. 
        
        st.markdown("#### Azure OpenAI Settings")
        
        # We need specific UI for Azure (Endpoint, Key, Deployment, Version)
        # We'll use a prefix 'azure_' for config keys
        
        # Load config
        az_endpoint = st.session_state.api_config.get("azure_endpoint", "")
        az_key = st.session_state.api_config.get("azure_key", "")
        az_deployment = st.session_state.api_config.get("azure_deployment", "")
        az_version = st.session_state.api_config.get("azure_version", "2024-02-15-preview")
        
        # Inputs
        c1, c2 = st.columns(2)
        with c1:
            ui_az_endpoint = st.text_input("Endpoint URL", value=az_endpoint, placeholder="https://resource.openai.azure.com/")
            ui_az_deployment = st.text_input("Deployment Name", value=az_deployment, placeholder="e.g. gpt-4-deploy")
        with c2:
            ui_az_key = st.text_input("API Key", value=az_key, type="password")
            ui_az_version = st.text_input("API Version", value=az_version, placeholder="2024-02-15-preview")
            
        if st.button("💾 Save Azure Settings", use_container_width=True):
            st.session_state.api_config["azure_endpoint"] = ui_az_endpoint
            st.session_state.api_config["azure_key"] = ui_az_key
            st.session_state.api_config["azure_deployment"] = ui_az_deployment
            st.session_state.api_config["azure_version"] = ui_az_version
            save_config(st.session_state.api_config)
            st.toast("Azure Settings Saved!", icon="✅")
            st.rerun()

        # Construct azure_config for analyzer
        azure_config = {
            "endpoint": ui_az_endpoint,
            "api_key": ui_az_key,
            "deployment_name": ui_az_deployment,
            "api_version": ui_az_version
        }
        
        # For Azure, the 'model list' is technically just the deployment name. 
        # To keep UI consistent, we can just show the deployment name as the single 'model'.
        available_models = [ui_az_deployment] if ui_az_deployment else ["Enter Deployment Name"]

    selected_model = st.selectbox(
        "AI Model", 
        available_models,
        index=0,
        key=f"selected_model_{provider_key}"
    )
    
    st.markdown("### 🛠 Advanced Parameters")
    temp_val = 0.1 # Fixed optimal temperature for focused analysis
    top_p_val = st.slider("Max Tokens", 100, 4000, 2000, 100)
    
    st.info(f"AI Provider: {provider}")
    st.markdown("---")
    st.markdown("### 📊 Active Analysis")
    st.caption("Status: Ready to analyze")
    if st.button("🧹 Clear App Cache"):
        st.cache_resource.clear()
        st.rerun()

st.markdown("# 🤖 AI Recruitment Intelligence Portal")
st.markdown("### Professional HR Candidate Analysis & Ranking")
st.markdown("---")

# Tabs Configuration
tabs = st.tabs(["Single Evaluation", "Batch Ranking", "📜 Analysis History", "Recruitment ChatBot", "Settings"])

with tabs[0]:
    st.subheader("Single Resume Evaluation")
    col1, col2 = st.columns([1, 1])
    
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
                        <div class="glass-card">
                            <p style="margin:0; opacity:0.7;">Match Confidence</p>
                            <h1 style="margin:0; font-size: 3rem;">{result.match_percentage}%</h1>
                        </div>
                        """, unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"""
                        <div class="glass-card">
                            <p style="margin:0; opacity:0.7;">Recommended Rank</p>
                            <h2 style="margin:0; color: #38bdf8;">{result.ranking}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    with m3:
                        st.markdown(f"""
                        <div class="glass-card">
                            <p style="margin:0; opacity:0.7;">Skills Match</p>
                            <h2 style="margin:0;">{len(result.matched_skills)} Found</h2>
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
    st.subheader("Batch Candidate Ranking")
    batch_jd = st.text_area("Job Description for Ranking", height=200, key="batch_jd")
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
            
            if results:
                df = pd.DataFrame(results)
                # Sort by score
                df = df.sort_values(by="match_percentage", ascending=False)
                
                st.subheader("Ranking Results")
                st.dataframe(df[['candidate_name', 'match_percentage', 'ranking', 'candidate_summary']], use_container_width=True)
                
                st.bar_chart(df.set_index('candidate_name')['match_percentage'])

with tabs[2]:
    st.subheader("📜 Evaluation History")
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
    st.subheader("🤖 Recruitment ChatBot")
    st.markdown("---")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(assistant_response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
            except Exception as e:
                st.error(f"Chat failed: {e}")

    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

with tabs[4]:
    st.subheader("System Health")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write(f"Active Provider: **{provider_key}**")
    if st.button("🔥 Run Health Check"):
        if provider_key == "Ollama":
            try:
                # Check if current Ollama URL is reachable with ngrok bypass
                headers = {
                    'ngrok-skip-browser-warning': 'true',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(f"{ollama_url}/api/tags", timeout=5, headers=headers)
                if response.status_code == 200:
                    models = [m['name'] for m in response.json().get('models', [])]
                    st.success(f"Connection to Ollama ({ollama_url}) is ONLINE.")
                    st.info(f"Available Models: {', '.join(models)}")
                else:
                    st.error(f"Ollama at {ollama_url} returned status code: {response.status_code}")
            except Exception as e:
                st.error(f"Ollama at {ollama_url} is OFFLINE: {e}")
        
        elif provider_key == "OpenAI":
            if not api_key_val:
                st.warning("Please enter an OpenAI API Key to test connection.")
            else:
                try:
                    # Simple check for model list
                    headers = {"Authorization": f"Bearer {api_key_val}"}
                    response = requests.get("https://api.openai.com/v1/models", timeout=5, headers=headers)
                    if response.status_code == 200:
                        st.success("Connection to OpenAI API is ONLINE.")
                    else:
                        st.error(f"OpenAI API Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Failed to reach OpenAI: {e}")

        elif provider_key == "Groq":
            if not api_key_val:
                st.warning("Please enter a Groq API Key to test connection.")
            else:
                try:
                    headers = {"Authorization": f"Bearer {api_key_val}"}
                    response = requests.get("https://api.groq.com/openai/v1/models", timeout=5, headers=headers)
                    if response.status_code == 200:
                        st.success("Connection to Groq API is ONLINE.")
                    else:
                        st.error(f"Groq API Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Failed to reach Groq: {e}")
        
        elif provider_key == "SarvamAI":
            if not api_key_val:
                st.warning("Please enter a Sarvam API Key.")
            else:
                try:
                    headers = {"Authorization": f"Bearer {api_key_val}"}
                    response = requests.get("https://api.sarvam.ai/v1/models", timeout=5, headers=headers)
                    if response.status_code == 200:
                        st.success("Connection to Sarvam AI is ONLINE.")
                    else:
                        st.error(f"Sarvam AI Error: {response.status_code}")
                except Exception as e:
                    st.error(f"Failed to reach Sarvam AI: {e}")

        elif provider_key == "DeepSeek":
            if not api_key_val:
                st.warning("Please enter a DeepSeek API Key.")
            else:
                try:
                    headers = {"Authorization": f"Bearer {api_key_val}"}
                    response = requests.get("https://api.deepseek.com/models", timeout=5, headers=headers)
                    if response.status_code == 200:
                        st.success("Connection to DeepSeek is ONLINE.")
                    else:
                        # DeepSeek might not support the same models endpoint or format, adjust as needed
                        st.error(f"DeepSeek Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Failed to reach DeepSeek: {e}")

        elif provider_key == "Gemini":
            if not api_key_val:
                st.warning("Please enter a Gemini API Key.")
            else:
                try:
                    # Simple check using requests to list models
                    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key_val}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        st.success("Connection to Google Gemini is ONLINE.")
                    else:
                        st.error(f"Gemini Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Failed to reach Gemini: {e}")

        elif provider_key == "AzureOpenAI":
            if not azure_config or not azure_config.get("api_key") or not azure_config.get("endpoint"):
                st.warning("Please configure Azure OpenAI settings.")
            else:
                try:
                    # Construct URL for model list or empty completion
                    # {endpoint}/openai/deployments?api-version={version}
                    endpoint = azure_config.get("endpoint").rstrip('/')
                    version = azure_config.get("api_version")
                    key = azure_config.get("api_key")
                    url = f"{endpoint}/openai/deployments?api-version={version}"
                    headers = {"api-key": key}
                    
                    response = requests.get(url, timeout=5, headers=headers)
                    if response.status_code == 200:
                         st.success("Connection to Azure OpenAI is ONLINE.")
                    else:
                        st.error(f"Azure Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Failed to reach Azure OpenAI: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

# Copyright Footer
st.markdown("""
    <div style="text-align: center; margin-top: 50px; padding: 20px; opacity: 0.5;">
        <p style="font-size: 12px;">© 2026 Bhadradri Technologies Inc. All Rights Reserved.</p>
        <p style="font-size: 11px;">HR Intelligence Assistant | Powered by AI | Version 1.7</p>
    </div>
""", unsafe_allow_html=True)
