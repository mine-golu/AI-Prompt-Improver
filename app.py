import os
import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Prompt Improver",
    page_icon="✨",
    layout="centered"
)

load_dotenv()

if "history" not in st.session_state:
    st.session_state.history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "latest_provider" not in st.session_state:
    st.session_state.latest_provider = None

# AI instructions
SYSTEM_INSTRUCTION = """
You are an expert AI prompt engineer.

Improve the user's rough prompt.

Rules:
1. Preserve the original intention.
2. Make the prompt clear and specific.
3. Add useful context and structure.
4. Do not answer or execute the original prompt.
5. Avoid unnecessary words.
6. Return a practical, ready-to-use prompt.
7. Briefly explain the main improvements.

Use this output format:

IMPROVED PROMPT:
[Write the improved prompt]

WHAT CHANGED:
[Briefly explain the improvements]
"""


def improve_with_gemini(user_message):
    api_key = st.secrets(GEMINI_API_KEY="")

    if not api_key:
        raise Exception("Gemini API key is missing.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.3,
            max_output_tokens=1000
        )
    )

    if not response.text:
        raise Exception("Gemini returned an empty response.")

    return response.text


def improve_with_openrouter(user_message):
    api_key = st.secrets(OPENROUTER_API_KEY="")

    if not api_key:
        raise Exception("OpenRouter API key is missing.")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "AI Prompt Improver"
    }

    payload = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90
    )

    response.raise_for_status()

    data = response.json()
    result = data["choices"][0]["message"]["content"]

    if not result:
        raise Exception("OpenRouter returned an empty response.")

    return result


def improve_prompt(user_message):
    errors = []

    # First try Gemini
    try:
        return improve_with_gemini(user_message), "Google Gemini"
    except Exception as e:
        errors.append(f"Gemini: {str(e)}")

    # Automatically switch to OpenRouter
    try:
        return improve_with_openrouter(user_message), "OpenRouter Free"
    except Exception as e:
        errors.append(f"OpenRouter: {str(e)}")

    raise Exception("Both AI providers failed:\n" + "\n".join(errors))


# Custom styling
st.markdown("""
<style>
    .main {
        background-color: #10121a;
    }
    .stButton > button {
        background-color: #7c5cff;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #6244df;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Application title
st.title("✨ AI Prompt Improver")
st.write("Transform rough prompts into clear, powerful AI prompts.")
st.caption("Powered by automatic AI model switching")
st.divider()

# User input
rough_prompt = st.text_area(
    "Enter your rough prompt:",
    placeholder="Example: Create a website for college students...",
    height=160
)

# Improvement styles
style = st.selectbox(
    "Choose improvement style:",
    ["Simple", "Professional", "Detailed"]
)

# Improve prompt button
if st.button("✨ Improve My Prompt", use_container_width=True):

    if not rough_prompt.strip():
        st.warning("Please enter a prompt first.")

    elif len(rough_prompt) > 10000:
        st.warning("Please keep your prompt under 10,000 characters.")

    else:
        user_message = f"""
Improvement style: {style}

Original prompt:
{rough_prompt}
"""

        try:
            with st.spinner("Trying AI models... Please wait"):
                result, provider = improve_prompt(user_message)

            st.session_state.latest_result = result
            st.session_state.latest_provider = provider

            st.session_state.history.append({
                "original": rough_prompt,
                "style": style,
                "improved": result,
                "provider": provider
            })

            st.success(f"Your prompt is ready! Powered by {provider}")

        except Exception as e:
            st.error("Unable to improve your prompt.")
            st.error(str(e))


# Display latest result
if st.session_state.latest_result:

    st.subheader("🚀 Improved Prompt")

    if st.session_state.latest_provider:
        st.caption(
            f"AI Provider: {st.session_state.latest_provider}"
        )

    st.markdown(st.session_state.latest_result)

    st.download_button(
        label="Download Improved Prompt",
        data=st.session_state.latest_result,
        file_name="improved_prompt.txt",
        mime="text/plain",
        use_container_width=True
    )


# Prompt history
st.divider()
st.subheader("📚 Prompt History")

if st.session_state.history:

    for i, item in enumerate(
        reversed(st.session_state.history), 1
    ):
        with st.expander(
            f"Prompt {i} - {item['style']}"
        ):
            st.markdown("**Original Prompt:**")
            st.write(item["original"])

            st.markdown("**Improved Result:**")
            st.markdown(item["improved"])

            st.caption(
                f"Provider: {item['provider']}"
            )

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.session_state.latest_provider = None
        st.rerun()

else:
    st.info("No prompt history available yet.")

st.divider()
st.caption("AI Prompt Improver | Major Project")