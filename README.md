# 🤖 AI Recruitment Intelligence Portal

A production-ready, AI-powered HR portal built to analyze resumes, rank candidates, and assist recruiters using local and cloud-based LLMs.

**GitHub Repository**: [https://github.com/Srk-1974/AI-Recruitment-Intelligence](https://github.com/Srk-1974/AI-Recruitment-Intelligence)

## 🌟 Key Features
- **Single Evaluation**: Instant 0-100% match score with skill gap analysis.
- **Batch Ranking**: Rank hundreds of resumes against one JD in seconds.
- **Recruitment ChatBot**: Interactive AI assistant to explain analysis and answer HR questions.
- **Multi-Model Support**: Use **Local Ollama** (llama3.2), **Groq** (Llama 3.3/DeepSeek), or **OpenAI**.
- **Premium UI**: Modern dark-mode "Glassmorphism" dashboard.

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** (Optional for local AI): [ollama.com](https://ollama.com)

### 2. Setup
```bash
git clone https://github.com/Srk-1974/AI-Recruitment-Intelligence.git
cd AI-Recruitment-Intelligence
pip install -r requirements.txt
```

### 3. Run
```bash
streamlit run app.py
```

## 🛠 Tech Stack
- **UI/Logic**: Streamlit (Standalone Architecture)
- **AI Orchestration**: LangChain
- **Parsers**: PyPDF, Python-Docx
- **Models**: Ollama, Groq, OpenAI

## 🌎 Public Release
To release to the public, connect this repository to **Streamlit Cloud** and use a Cloud AI token (Groq/OpenAI) in the settings.

---
Built with ❤️ for AI-driven Recruitment.
