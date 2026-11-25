import os
import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Prompt Improver",
    page_icon="✨",
    layout="centered"
)

load_dotenv()


# ==========================================
# API KEY CONFIGURATION
# ==========================================

def get_api_key(key_name):
    """Load API key from Streamlit Secrets or environment."""

    try:
        key = st.secrets.get(key_name, "")
        if key:
            return key
    except Exception:
        pass

    return os.getenv(key_name, "")


# ==========================================
# SESSION STATE
# ==========================================

if "history" not in st.session_state:
    st.session_state.history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

if "latest_provider" not in st.session_state:
    st.session_state.latest_provider = None


# ==========================================
# AI SYSTEM INSTRUCTIONS
# ==========================================

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


# ==========================================
# GEMINI AI FUNCTION
# ==========================================

def improve_with_gemini(user_message):

    api_key = get_api_key("GEMINI_API_KEY")

    if not api_key:
        raise Exception("Gemini API key is missing.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
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


# ==========================================
# OPENROUTER AI FUNCTION
# ==========================================

def improve_with_openrouter(user_message):

    api_key = get_api_key("OPENROUTER_API_KEY")

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

    if response.status_code != 200:
        raise Exception(
            f"OpenRouter HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    data = response.json()

    if "choices" not in data or not data["choices"]:
        raise Exception("OpenRouter returned no choices.")

    result = data["choices"][0]["message"]["content"]

    if not result:
        raise Exception("OpenRouter returned an empty response.")

    return result


# ==========================================
# AUTOMATIC AI FALLBACK SYSTEM
# ==========================================

def improve_prompt(user_message):

    errors = []

    # First: Try Gemini
    try:
        result = improve_with_gemini(user_message)
        return result, "Google Gemini"

    except Exception as e:
        errors.append(f"Gemini: {str(e)}")

    # Second: Automatically try OpenRouter
    try:
        result = improve_with_openrouter(user_message)
        return result, "OpenRouter Free"

    except Exception as e:
        errors.append(f"OpenRouter: {str(e)}")

    # Both providers failed
    raise Exception(
        "Both AI providers failed:\n\n"
        + "\n".join(errors)
    )


# ==========================================
# CUSTOM CSS
# ==========================================

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


# ==========================================
# APPLICATION TITLE
# ==========================================

st.title("✨ AI Prompt Improver")

st.write(
    "Transform rough prompts into clear, powerful AI prompts."
)

st.caption(
    "Powered by automatic AI model switching"
)

st.divider()


# ==========================================
# USER INPUT
# ==========================================

rough_prompt = st.text_area(
    "Enter your rough prompt:",
    placeholder="Example: Create a website for college students...",
    height=160
)


# ==========================================
# IMPROVEMENT STYLE
# ==========================================

style = st.selectbox(
    "Choose improvement style:",
    ["Simple", "Professional", "Detailed"]
)


# ==========================================
# IMPROVE PROMPT BUTTON
# ==========================================

if st.button(
    "✨ Improve My Prompt",
    use_container_width=True
):

    if not rough_prompt.strip():

        st.warning("Please enter a prompt first.")

    elif len(rough_prompt) > 10000:

        st.warning(
            "Please keep your prompt under 10,000 characters."
        )

    else:

        user_message = f"""
Improvement style: {style}

Original prompt:
{rough_prompt}
"""

        try:

            with st.spinner(
                "Trying AI models... Please wait"
            ):

                result, provider = improve_prompt(
                    user_message
                )

            st.session_state.latest_result = result
            st.session_state.latest_provider = provider

            st.session_state.history.append({
                "original": rough_prompt,
                "style": style,
                "improved": result,
                "provider": provider
            })

            st.success(
                f"Your prompt is ready! Powered by {provider}"
            )

        except Exception as e:

            st.error("Unable to improve your prompt.")

            st.error(str(e))


# ==========================================
# DISPLAY LATEST RESULT
# ==========================================

if st.session_state.latest_result:

    st.subheader("🚀 Improved Prompt")

    if st.session_state.latest_provider:

        st.caption(
            f"AI Provider: {st.session_state.latest_provider}"
        )

    st.markdown(
        st.session_state.latest_result
    )

    st.download_button(
        label="Download Improved Prompt",
        data=st.session_state.latest_result,
        file_name="improved_prompt.txt",
        mime="text/plain",
        use_container_width=True
    )


# ==========================================
# PROMPT HISTORY
# ==========================================

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


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "AI Prompt Improver | Major Project"
)