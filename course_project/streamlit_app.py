import os
import sys
import tempfile

import streamlit as st


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from course_project.engine import DungeonMasterEngine


def synthesize_speech(text: str, rate: int = 180) -> bytes | None:
    """Generate WAV audio for DM narration using local text-to-speech."""
    try:
        import pyttsx3
    except Exception:
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        audio_path = temp_file.name

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", rate)
        engine.save_to_file(text, audio_path)
        engine.runAndWait()

        with open(audio_path, "rb") as audio_file:
            return audio_file.read()
    except Exception:
        return None
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


st.set_page_config(page_title="AI Dungeon Master", page_icon="d20", layout="wide")
st.title("AI Dungeon Master Project")
st.caption("Templates, tools, planning, RAG, and memory")


if "engine" not in st.session_state:
    st.session_state.engine = DungeonMasterEngine()
    st.session_state.session_id = st.session_state.engine.start_session(player_name="StreamlitPlayer")
    st.session_state.indexed_chunks = st.session_state.engine.index_default_lore()

if "chat" not in st.session_state:
    st.session_state.chat = []

with st.sidebar:
    st.subheader("Model Controls")
    scenario = st.selectbox(
        "Scenario",
        [
            "tavern_social",
            "dungeon_exploration",
            "combat_resolution",
            "merchant_bargain",
            "quest_tracking",
        ],
        index=0,
    )
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.4, step=0.05)
    max_tokens = st.slider("Max Tokens", min_value=100, max_value=1200, value=500, step=50)

    st.subheader("Innovation Add-on")
    enable_tts = st.checkbox("Enable DM text-to-speech", value=False)
    tts_rate = st.slider("Speech Rate", min_value=120, max_value=240, value=180, step=10, disabled=not enable_tts)

    st.write(f"Indexed lore chunks: {st.session_state.indexed_chunks}")

    if st.button("Re-index Lore"):
        st.session_state.indexed_chunks = st.session_state.engine.index_default_lore()
        st.success(f"Re-indexed {st.session_state.indexed_chunks} chunks")

for role, message in st.session_state.chat:
    with st.chat_message(role):
        st.write(message)

user_message = st.chat_input("Describe your action or ask the DM...")
if user_message:
    st.session_state.chat.append(("user", user_message))
    with st.chat_message("user"):
        st.write(user_message)

    result = st.session_state.engine.process_turn(
        session_id=st.session_state.session_id,
        user_message=user_message,
        scenario=scenario,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    dm_message = result["response"]
    st.session_state.chat.append(("assistant", dm_message))
    with st.chat_message("assistant"):
        st.write(dm_message)
        if enable_tts:
            audio_bytes = synthesize_speech(dm_message, rate=tts_rate)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
            else:
                st.info("Text-to-speech unavailable. Install pyttsx3 in your environment.")

    with st.expander("Planning + Retrieval Details"):
        st.write("Turn Plan:")
        st.json(result["plan"])
        st.write("Retrieved Context Chunks:")
        st.write(result["context"])
        st.write("Tool Notes:")
        st.write(result["tool_notes"])
