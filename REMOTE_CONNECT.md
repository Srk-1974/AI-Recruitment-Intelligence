# 🌐 Remote Connection Guide: Laptop to Portal

This guide explains how to connect your **local laptop AI (Ollama)** to your **Public HR Portal (Cloud)**.

## 🚀 The Core Command
To create a secure bridge between your laptop and the website, run this command in your terminal (PowerShell or CMD):

```bash
ngrok http 11434 --host-header="localhost:11434"
```

---

## 📋 Step-by-Step Instructions

### 1. Requirements
- **Ollama**: Must be running on your laptop.
- **Ngrok**: Installed on your laptop ([Download here](https://ngrok.com/download)).

### 2. Start the Tunnel
1.  Open your Terminal.
2.  Run the command: `ngrok http 11434 --host-header="localhost:11434"`
3.  Copy the **Forwarding** URL (it starts with `https://` and ends with `.ngrok-free.app` or `.ngrok-free.dev`).

### 3. Configure the Portal
1.  Open your [HR Recruitment Portal](https://ai-recruitment-intelligence-qsfkwmpewnannjnade3apb.streamlit.app/).
2.  In the status sidebar, select **Ollama (Local PC)**.
3.  Paste your **Ngrok URL** into the "Local Ollama URL" box.
4.  Wait 2 seconds for your local models (like `llama3.2`) to appear in the dropdown.

### 4. Verify Connection
- Go to the **Settings** tab.
- Click **🔥 Run Health Check**.
- You should see: `✅ Connection to Ollama is ONLINE`.

---

## ⚠️ Important Notes
- **Keep Terminal Open**: If you close the Ngrok terminal window, the connection to the portal will stop.
- **New Links**: Every time you restart Ngrok, it might provide a new URL. Remember to update the URL in the portal sidebar if it changes.
- **Privacy**: Only share your Ngrok link with people you trust, as it provides a path to your local Ollama API.
