# 🤖 Gemini Chatbot

A simple AI chatbot built with **Streamlit** and **Google Gemini**.

## Features
- Chat interface with conversation memory (multi-turn)
- Streaming responses (text appears as it's generated)
- Clear chat button
- API key kept in Streamlit secrets (not in code)

## Tech stack
- Python, Streamlit (UI + hosting)
- Google Gemini API via the `google-genai` SDK

## Run locally
```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your key
streamlit run app.py
```
Get a free API key at https://aistudio.google.com/apikey

## Deploy (Streamlit Community Cloud)
1. Push this folder to a public GitHub repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, pick the repo, branch `main`, main file `app.py`.
4. Open **Advanced settings → Secrets** and add:
   ```toml
   GEMINI_API_KEY = "your-key-here"
   ```
5. Click **Deploy**. You'll get a public link like `https://your-app.streamlit.app`.
