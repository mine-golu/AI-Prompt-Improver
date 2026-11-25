import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Must be the first Streamlit command
st.set_page_config(
    page_title="AI Prompt Improver",
    page_icon="✨",
    layout="centered"
)

# Load API key from .env
load_dotenv()

if "history" not in st.session_state:
    st.session_state.history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

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
    [
        "Simple",
        "Professional",
        "Detailed"
    ]
)

# Improve prompt button
if st.button("✨ Improve My Prompt", use_container_width=True):
    if not rough_prompt.strip():
        st.warning("Please enter a prompt first.")
    elif len(rough_prompt) > 10000:
        st.warning("Please keep your prompt under 10,000 characters.")
    else:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error("API key not found. Check your .env file.")
        else:
            try:
                client = genai.Client(api_key=api_key)

                system_instruction = """
You are an expert AI prompt engineer.

Your task is to improve the user's rough prompt.

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

                user_message = f"""
Improvement style: {style}

Original prompt:
{rough_prompt}
"""

                with st.spinner("Improving your prompt..."):
                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=user_message,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                            max_output_tokens=1000
                        )
                    )

                result = response.text

                if result:
                    st.session_state.latest_result = result
                    st.session_state.history.append({
                        "original": rough_prompt,
                        "style": style,
                        "improved": result
                    })
                    st.success("Your prompt is ready!")
                else:
                    st.error("The AI returned an empty response.")

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# Display latest result (persists even after clicking Download)
if st.session_state.latest_result:
    st.subheader("🚀 Improved Prompt")
    st.markdown(st.session_state.latest_result)

    st.download_button(
        label="Download Improved Prompt",
        data=st.session_state.latest_result,
        file_name="improved_prompt.txt",
        mime="text/plain",
        use_container_width=True
    )

# Prompt history section
st.divider()
st.subheader("📚 Prompt History")

if st.session_state.history:
    for i, item in enumerate(reversed(st.session_state.history), 1):
        with st.expander(f"Prompt {i} - {item['style']}"):
            st.markdown("**Original Prompt:**")
            st.write(item["original"])

            st.markdown("**Improved Result:**")
            st.markdown(item["improved"])

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.latest_result = None
        st.rerun()
else:
    st.info("No prompt history available yet.")

st.divider()
st.caption("AI Prompt Improver | Major Project")