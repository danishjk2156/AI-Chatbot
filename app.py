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


MODEL = get_secret("GEMINI_MODEL", "gemini-2.5-flash")
SYSTEM_PROMPT = "You are a friendly, helpful assistant. Keep answers clear and concise."

with st.sidebar:
    st.header("Settings")
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        api_key = st.text_input("Gemini API key", type="password")
        st.caption("Get a free key at https://aistudio.google.com/apikey")
    if st.button("Clear chat"):
        st.session_state.messages = []
    st.caption(f"Model: {MODEL}")

st.title("🤖 Gemini Chatbot")
st.caption("A simple chatbot built with Streamlit and Google Gemini.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Type your message...")

if prompt:
    if not api_key:
        st.warning("Please enter your Gemini API key in the sidebar.")
        st.stop()

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
