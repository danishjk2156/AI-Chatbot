import os

import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Gemini Chatbot", page_icon="🤖")


def get_secret(name, default=None):
    # st.secrets raises if no secrets file exists, so fall back quietly
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# Optional: pin a model in secrets, otherwise the newest available one is selected
DEFAULT_MODEL = get_secret("GEMINI_MODEL")
FALLBACK_MODEL = "gemini-2.5-flash"
SYSTEM_PROMPT = "You are a friendly, helpful assistant. Keep answers clear and concise."


def find_api_key():
    # Accept the key at the top level, inside any [section], or as an env var
    key = get_secret("GEMINI_API_KEY")
    if key:
        return key
    try:
        for value in st.secrets.values():
            if hasattr(value, "get") and value.get("GEMINI_API_KEY"):
                return value.get("GEMINI_API_KEY")
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY")


def secret_names():
    try:
        return list(st.secrets.keys())
    except Exception:
        return []


api_key = find_api_key()


@st.cache_data(ttl=3600, show_spinner=False)
def list_chat_models(key):
    # Ask Gemini which text chat models this key can use, newest first
    # Keep the client in a variable: if it's garbage-collected mid-listing the request fails
    client = genai.Client(api_key=key)
    try:
        names = [
            m.name.removeprefix("models/")
            for m in client.models.list()
            if "generateContent" in (m.supported_actions or [])
            and m.name.startswith("models/gemini")
            and not any(x in m.name for x in ("tts", "image", "audio", "live"))
        ]
        return sorted(names, reverse=True), None
    except Exception as e:
        return [], str(e)


st.title("🤖 Gemini Chatbot")
st.caption("A simple chatbot built with Streamlit and Google Gemini.")

if not api_key:
    st.error("GEMINI_API_KEY is not set. Add it to .streamlit/secrets.toml or the Streamlit Cloud app's Secrets.")
    st.caption(f"Secret names the app can see: {secret_names() or 'none'}")
    st.stop()

with st.sidebar:
    st.header("Settings")
    models, list_error = list_chat_models(api_key)
    if list_error:
        st.warning(f"Couldn't load the model list from Google, using the default model. Reason: {list_error[:200]}")
    models = models or [DEFAULT_MODEL or FALLBACK_MODEL]
    index = models.index(DEFAULT_MODEL) if DEFAULT_MODEL in models else 0
    MODEL = st.selectbox("Model", models, index=index)
    if st.button("Clear chat"):
        st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini calls the assistant role "model"
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in st.session_state.messages
    ]

    client = genai.Client(api_key=api_key)

    def stream_reply():
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
        ):
            if chunk.text:
                yield chunk.text

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(stream_reply())
        except Exception as e:
            st.error(f"Error from Gemini: {e}")
            st.session_state.messages.pop()
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": reply})
