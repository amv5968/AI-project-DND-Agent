import os
import sys
import tempfile
from io import BytesIO
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import streamlit as st
from PIL import Image, ImageDraw


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from course_project.engine import DungeonMasterEngine


def synthesize_speech(text: str, rate: int = 180) -> bytes | None:
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


def build_scene_image_url(scene_text: str, style: str, seed: int, width: int, height: int) -> str:
    prompt = f"{style} fantasy illustration, tabletop RPG scene, cinematic lighting: {scene_text[:500]}"
    return (
        f"https://image.pollinations.ai/prompt/{quote_plus(prompt)}"
        f"?seed={seed}&width={width}&height={height}&nologo=true"
    )


def generate_fallback_image(scene_text: str, width: int, height: int) -> bytes:
    image = Image.new("RGB", (width, height), color=(28, 35, 54))
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, width - 16, height - 16), outline=(120, 150, 220), width=3)

    title = "Scene Image (Fallback)"
    description = scene_text[:180] + ("..." if len(scene_text) > 180 else "")
    draw.text((28, 28), title, fill=(236, 240, 255))
    draw.text((28, 68), description, fill=(210, 218, 240))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_scene_image(scene_text: str, style: str, seed: int, width: int, height: int) -> tuple[bytes, str | None]:
    image_url = build_scene_image_url(
        scene_text=scene_text,
        style=style,
        seed=seed,
        width=width,
        height=height,
    )

    request = Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=25) as response:
            return response.read(), None
    except Exception as e:
        return generate_fallback_image(scene_text, width, height), f"Remote image service unavailable ({e}). Showing local fallback image."


st.set_page_config(page_title="AI Dungeon Master", page_icon="d20", layout="wide")
st.title("AI Dungeon Master Project")
st.caption("Templates, tools, planning, RAG, and memory")


if "engine" not in st.session_state:
    st.session_state.engine = DungeonMasterEngine()
    st.session_state.session_id = st.session_state.engine.start_session(player_name="StreamlitPlayer")
    st.session_state.indexed_chunks = st.session_state.engine.index_default_lore()

if "chat" not in st.session_state:
    st.session_state.chat = []

if "image_seed" not in st.session_state:
    st.session_state.image_seed = 1

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

    enable_scene_images = st.checkbox("Enable scene image generation", value=False)
    image_style = st.selectbox(
        "Image Style",
        ["epic fantasy art", "watercolor fantasy", "pixel art", "dark gothic painting", "storybook illustration"],
        index=0,
        disabled=not enable_scene_images,
    )
    image_width = st.slider("Image Width", min_value=512, max_value=1024, value=768, step=128, disabled=not enable_scene_images)
    image_height = st.slider("Image Height", min_value=512, max_value=1024, value=768, step=128, disabled=not enable_scene_images)
    if st.button("Regenerate Next Image", disabled=not enable_scene_images):
        st.session_state.image_seed += 1

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

        if enable_scene_images:
            image_bytes, image_notice = generate_scene_image(
                scene_text=dm_message,
                style=image_style,
                seed=st.session_state.image_seed,
                width=image_width,
                height=image_height,
            )
            st.image(image_bytes, caption="Generated scene image", width="stretch")
            if image_notice:
                st.warning(image_notice)

    with st.expander("Planning + Retrieval Details"):
        st.write("Turn Plan:")
        st.json(result["plan"])
        st.write("Retrieved Context Chunks:")
        st.write(result["context"])
        st.write("Tool Notes:")
        st.write(result["tool_notes"])