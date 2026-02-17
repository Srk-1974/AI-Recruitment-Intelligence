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
st.set_page_config(page_title="Intelligent HR Assistant", layout="wide", page_icon="💠", initial_sidebar_state="expanded")

# Version: 1.7.2 - Full Parameter Fix (Sync: 2026-02-16)
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
                background: linear-gradient(135deg, #4c1d95, #6d28d9);
                padding: 20px 50px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(109, 40, 217, 0.4);
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
                            color: #a78bfa;
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
            <h2 style="margin-top: 25px; font-size: 24px; color: #c4b5fd;">HR Intelligence Assistant</h2>
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
        border-color: rgba(167, 139, 250, 0.4);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Custom Tags */
    .skill-tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 20px;
        background: rgba(139, 92, 246, 0.1);
        color: #a78bfa;
        border: 1px solid rgba(167, 139, 250, 0.3);
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
        background: linear-gradient(90deg, #7c3aed 0%, #6d28d9 100%);
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
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
    }

    /* Headers */
    h1 {
        background: linear-gradient(90deg, #a78bfa, #c4b5fd);
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
                background: linear-gradient(135deg, #4c1d95, #6d28d9);
                padding: 8px 15px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(109, 40, 217, 0.3);
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
                            color: #a78bfa;
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
    # Note about Engine Settings
    st.markdown("---")
    st.info("⚙️ **Engine Settings** have moved to the **Settings** tab.")
    
    st.markdown("### 🚑 System Tools")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧼 Clear Cache", use_container_width=True):
            st.cache_resource.clear()
            st.toast("Cache Cleared!")
    with c2:
        if st.button("🔥 Health Check", use_container_width=True):
            st.info(f"Connected to: {st.session_state.current_provider}")

# Initialize Engine Variables at top level (accessible to all tabs)
# Use session state to persist choices
if "current_provider" not in st.session_state:
    st.session_state.current_provider = "Ollama (Local PC)"
if "current_model" not in st.session_state:
    st.session_state.current_model = "llama3.2"
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

st.markdown("# 💠 AI Recruitment Intelligence Portal")
st.markdown("### Professional HR Candidate Analysis & Ranking")
st.markdown("---")

# Tabs Configuration
tabs = st.tabs(["📄 Single Evaluation", "👥 Batch Ranking", "📜 Analysis History", "💬 Recruitment ChatBot", "⚙️ Admin Settings"])

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
    st.subheader("💠 Recruitment ChatBot")
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
    # --- PROMOTED ENGINE SETTINGS (Now in Tabs instead of Sidebar) ---
    st.subheader("🛡️ Recruitment Intelligence Control Center")
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
        st.markdown("### 💠 Model & Provider Selection")
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
    <div style="text-align: center; margin-top: 50px; padding: 20px; opacity: 0.5;">
        <p style="font-size: 12px;">© 2026 Bhadradri Technologies Inc. All Rights Reserved.</p>
        <p style="font-size: 11px;">HR Intelligence Assistant | Powered by AI | Version 1.7</p>
    </div>
""", unsafe_allow_html=True)
