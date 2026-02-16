# Walkthrough - AI Recruitment Intelligence Portal

I have built a complete, production-ready HR Assistant that automates the process of comparing resumes against job descriptions.

**GitHub Repository**: [Srk-1974/AI-Recruitment-Intelligence](https://github.com/Srk-1974/AI-Recruitment-Intelligence)

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.10+**
- **Ollama**: Install from [ollama.com](https://ollama.com) and pull a model:
  ```bash
  ollama pull llama3.2
  ```

### 2. Installation
Install the project dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running the Application
The app is now **Standalone** and does not require a separate backend terminal.

**Local Run:**
```bash
streamlit run app.py
```

**🌐 Public Demo:**
You can access the live version here:
👉 **[AI Recruitment Intelligence](https://ai-recruitment-intelligence-qsfkwmpewnannjnade3apb.streamlit.app/)**
*(Password: srk123)*

## 🛠 Project Structure

- **[app.py](file:///e:/Anti_gravity/Hr_module_localLLMALLM/app.py)**: The main entry point. Now standalone—it handles AI logic internally for cloud compatibility and production security.
- **core/**
  - **[parser.py](file:///e:/Anti_gravity/Hr_module_localLLMALLM/core/parser.py)**: PDF/Docx text extraction using `pypdf` and `python-docx`.
  - **[analyzer.py](file:///e:/Anti_gravity/Hr_module_localLLMALLM/core/analyzer.py)**: The heart of the AI—handles prompts and structured JSON parsing via `LangChain`.
  - **[models.py](file:///e:/Anti_gravity/Hr_module_localLLMALLM/core/models.py)**: Pydantic definitions for consistent data structures.
- **[app.py](file:///e:/Anti_gravity/Hr_module_localLLMALLM/app.py)**: Premium Streamlit interface with support for single and batch evaluations.

## 🌟 Key Features

### 🛒 Single Evaluation
Upload a resume and paste a JD to get:
- **Match Score**: A realistic 0-100% metric.
- **Skill Mapping**: Automatic identification of matching and missing skills.
- **AI Summary**: A professional executive summary of the candidate's fit.
- **Experience Audit**: Analysis of years of experience vs. requirements.

### 📊 Batch Candidate Ranking
Compare multiple candidates at once!
- Upload folder of resumes.
- View a ranked leaderboard.
- Visualize match scores in bar charts for quick decision-making.

### ❓ AI-Generated Interview Questions
Get a head start on your interviews!
- Tailored assessment questions for each candidate.
- Focus on validating skills and probing potential weaknesses.
- Professional, expert-level HR queries generated in real-time.

### 📜 Analysis History
Never lose track of your work!
- **Automatic Logging**: Every evaluation (single or batch) is saved to your session.
- **Data Table**: View a clear list of names, scores, and rankings.
- **Deep Dive**: Click "View Details" on any past entry to reload the full AI analysis.

## 🔍 How it Works (AI Logic)

The system uses a sophisticated prompt that instructs the LLM to act as an "Expert HR Assistant". 
1. **Extraction**: Text is pulled from binary formats (PDF/DOCX).
2. **Contextual Analysis**: Both the Resume and JD are injected into a prompt template.
3. **Structured Output**: The LLM is forced to return valid JSON, which is then validated by Pydantic before being displayed.

---
> [!TIP]
> You can switch models (e.g., from `llama3.2` to `mistral`) in the **Settings** tab of the UI without restarting the server!
