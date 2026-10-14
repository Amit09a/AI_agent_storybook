import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from pipeline import run_story_pipeline

load_dotenv()

OUTPUT_DIR = Path("outputs")

st.set_page_config(
    page_title="Storybook AI",
    page_icon="📚",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 🎨 Fairytale dark theme (appearance only)
# ---------------------------------------------------------------------------
FAIRYTALE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700;900&family=Fredoka:wght@400;500;600&display=swap');

:root {
    --night-1: #0b0a2a;
    --night-2: #1a1145;
    --night-3: #2b1b5e;
    --gold: #ffd86b;
    --gold-soft: #ffe9a8;
    --pink: #ff7eb6;
    --purple: #a78bfa;
    --mint: #7ee8c7;
    --card: rgba(30, 22, 80, 0.72);
    --card-border: rgba(255, 216, 107, 0.35);
    --text: #f3ecff;
}

/* ---------- Background: enchanted night sky ---------- */
.stApp {
    background:
        radial-gradient(ellipse at 15% 10%, rgba(167, 139, 250, 0.28) 0%, transparent 45%),
        radial-gradient(ellipse at 85% 20%, rgba(255, 126, 182, 0.18) 0%, transparent 40%),
        radial-gradient(ellipse at 50% 100%, rgba(126, 232, 199, 0.14) 0%, transparent 50%),
        linear-gradient(180deg, var(--night-1) 0%, var(--night-2) 55%, var(--night-3) 100%);
    background-attachment: fixed;
    font-family: 'Fredoka', sans-serif;
    color: var(--text);
}

/* Twinkling stars */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(2px 2px at 10% 20%, #fff, transparent),
        radial-gradient(1.5px 1.5px at 25% 70%, #ffe9a8, transparent),
        radial-gradient(2px 2px at 40% 35%, #fff, transparent),
        radial-gradient(1.5px 1.5px at 55% 85%, #fff, transparent),
        radial-gradient(2.5px 2.5px at 70% 15%, #ffe9a8, transparent),
        radial-gradient(1.5px 1.5px at 82% 55%, #fff, transparent),
        radial-gradient(2px 2px at 92% 80%, #ffe9a8, transparent),
        radial-gradient(1.5px 1.5px at 5% 90%, #fff, transparent),
        radial-gradient(2px 2px at 65% 50%, #fff, transparent),
        radial-gradient(1.5px 1.5px at 33% 8%, #ffe9a8, transparent);
    background-size: 100% 100%;
    animation: twinkle 4s ease-in-out infinite alternate;
}

@keyframes twinkle {
    0%   { opacity: 0.35; }
    100% { opacity: 1; }
}

[data-testid="stHeader"] { background: transparent; }
[data-testid="stAppViewContainer"] > .main,
[data-testid="stMain"] { position: relative; z-index: 1; }

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* ---------- Floating magical decorations ---------- */
.magic-float {
    position: fixed;
    pointer-events: none;
    z-index: 0;
    opacity: 0.85;
    animation: floaty 7s ease-in-out infinite;
    filter: drop-shadow(0 0 10px rgba(255, 216, 107, 0.6));
}
.magic-float.f1 { top: 12%; left: 4%;  font-size: 2.2rem; animation-delay: 0s; }
.magic-float.f2 { top: 28%; right: 5%; font-size: 2.6rem; animation-delay: 1.2s; }
.magic-float.f3 { top: 62%; left: 3%;  font-size: 2rem;   animation-delay: 2.4s; }
.magic-float.f4 { top: 75%; right: 4%; font-size: 2.4rem; animation-delay: 3.4s; }
.magic-float.f5 { top: 45%; left: 94%; font-size: 1.8rem; animation-delay: 4.4s; }

@keyframes floaty {
    0%, 100% { transform: translateY(0) rotate(-6deg); }
    50%      { transform: translateY(-22px) rotate(8deg); }
}

/* ---------- Hero title ---------- */
.hero {
    text-align: center;
    padding: 1.2rem 1rem 0.4rem 1rem;
}
.hero h1 {
    font-family: 'Cinzel Decorative', cursive;
    font-weight: 900;
    font-size: clamp(2.4rem, 6vw, 4.2rem);
    margin: 0;
    background: linear-gradient(90deg, var(--gold), var(--pink), var(--purple), var(--gold));
    background-size: 300% auto;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 6s linear infinite;
    text-shadow: 0 0 30px rgba(255, 216, 107, 0.25);
}
@keyframes shimmer {
    to { background-position: 300% center; }
}
.hero p {
    font-size: 1.2rem;
    color: var(--gold-soft);
    margin-top: 0.6rem;
}
.hero .castle {
    font-size: 2.6rem;
    letter-spacing: 0.6rem;
    margin-bottom: 0.2rem;
    animation: floaty 6s ease-in-out infinite;
}

/* ---------- Headings ---------- */
h1, h2, h3, h4 {
    font-family: 'Cinzel Decorative', cursive !important;
    color: var(--gold) !important;
    text-shadow: 0 0 18px rgba(255, 216, 107, 0.3);
}
h2 { text-align: center; }

p, label, span, li, .stMarkdown, [data-testid="stCaptionContainer"] {
    font-family: 'Fredoka', sans-serif;
}
[data-testid="stCaptionContainer"] {
    color: #cbbcf5 !important;
    font-size: 0.95rem;
}
strong { color: var(--gold-soft); }

/* ---------- Info / success / warning boxes ---------- */
[data-testid="stAlert"] {
    background: var(--card) !important;
    border: 2px dashed var(--card-border) !important;
    border-radius: 22px !important;
    color: var(--text) !important;
    backdrop-filter: blur(6px);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
}
[data-testid="stAlert"] p { color: var(--text) !important; font-size: 1.05rem; }

/* ---------- Text area (the story scroll) ---------- */
[data-testid="stTextArea"] label p {
    color: var(--gold) !important;
    font-size: 1.25rem !important;
    font-weight: 600;
}
[data-testid="stTextArea"] textarea {
    background: rgba(18, 12, 55, 0.85) !important;
    color: var(--text) !important;
    border: 2px solid var(--card-border) !important;
    border-radius: 22px !important;
    font-family: 'Fredoka', sans-serif !important;
    font-size: 1.1rem !important;
    padding: 1rem 1.2rem !important;
    box-shadow: inset 0 0 25px rgba(167, 139, 250, 0.15);
    transition: all 0.25s ease;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--pink) !important;
    box-shadow: 0 0 0 3px rgba(255, 126, 182, 0.3), 0 0 28px rgba(255, 126, 182, 0.35) !important;
}
[data-testid="stTextArea"] textarea::placeholder {
    color: #9b8fd0 !important;
    font-style: italic;
}

/* ---------- Checkbox ---------- */
[data-testid="stCheckbox"] label p {
    color: var(--text) !important;
    font-size: 1.05rem;
}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:first-child {
    border-radius: 8px !important;
    border-color: var(--gold) !important;
}

/* ---------- Buttons ---------- */
.stButton > button,
.stDownloadButton > button {
    font-family: 'Fredoka', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.25rem !important;
    color: #2a1250 !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 0.85rem 1.6rem !important;
    background: linear-gradient(135deg, var(--gold) 0%, var(--pink) 100%) !important;
    box-shadow: 0 6px 0 #b9467f, 0 12px 30px rgba(255, 126, 182, 0.45);
    transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.2s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-3px) scale(1.02);
    filter: brightness(1.08);
    box-shadow: 0 9px 0 #b9467f, 0 18px 40px rgba(255, 216, 107, 0.55);
    color: #2a1250 !important;
}
.stButton > button:active,
.stDownloadButton > button:active {
    transform: translateY(4px);
    box-shadow: 0 2px 0 #b9467f, 0 6px 14px rgba(255, 126, 182, 0.4);
}
.stDownloadButton > button {
    background: linear-gradient(135deg, var(--mint) 0%, var(--gold) 100%) !important;
    box-shadow: 0 6px 0 #3aa588, 0 12px 30px rgba(126, 232, 199, 0.4);
}
.stDownloadButton > button:hover {
    box-shadow: 0 9px 0 #3aa588, 0 18px 40px rgba(126, 232, 199, 0.5);
}
.stButton > button p,
.stDownloadButton > button p { color: #2a1250 !important; font-weight: 600; }

/* ---------- Spinner ---------- */
[data-testid="stSpinner"] {
    background: var(--card);
    border: 2px dashed var(--card-border);
    border-radius: 20px;
    padding: 0.9rem 1.2rem;
}
[data-testid="stSpinner"] p { color: var(--gold-soft) !important; font-size: 1.1rem; }

/* ---------- Divider ---------- */
hr {
    border: none !important;
    height: 3px !important;
    background: linear-gradient(90deg, transparent, var(--gold), var(--pink), var(--gold), transparent) !important;
    border-radius: 3px;
    margin: 2rem 0 !important;
    opacity: 0.9;
}

/* ---------- Storybook images ---------- */
[data-testid="stImage"] img {
    border-radius: 22px !important;
    border: 4px solid var(--gold) !important;
    box-shadow: 0 0 0 6px rgba(255, 216, 107, 0.15), 0 14px 38px rgba(0, 0, 0, 0.55), 0 0 30px rgba(167, 139, 250, 0.35);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
[data-testid="stImage"] img:hover {
    transform: scale(1.03) rotate(-0.6deg);
    box-shadow: 0 0 0 6px rgba(255, 126, 182, 0.3), 0 20px 50px rgba(0, 0, 0, 0.6), 0 0 40px rgba(255, 126, 182, 0.5);
}
[data-testid="stImage"] { text-align: center; }
[data-testid="stImage"] > div { display: flex; justify-content: center; }

/* Exception box (errors) */
[data-testid="stException"] { border-radius: 18px; }

/* Scrollbar */
::-webkit-scrollbar { width: 10px; }
::-webkit-scrollbar-track { background: var(--night-1); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--purple), var(--pink));
    border-radius: 10px;
}
</style>

<div class="magic-float f1">⭐</div>
<div class="magic-float f2">🌙</div>
<div class="magic-float f3">🧚</div>
<div class="magic-float f4">🦄</div>
<div class="magic-float f5">✨</div>
"""

st.markdown(FAIRYTALE_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <div class="castle">🏰 🐉 🌟</div>
        <h1>📚 Storybook AI</h1>
        <p>Turn your imagination into a beautifully illustrated
        five-page children's storybook.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "Enter a story idea below. The app will generate the story, "
    "illustrations, and a downloadable PDF."
)

prompt = st.text_area(
    "Your story idea",
    placeholder=(
        "Example: A little fox discovers a magical garden "
        "and learns the importance of friendship."
    ),
    height=130,
)

demo_mode = st.checkbox(
    "Use offline demo (no AI API calls)",
    value=False,
    help="Uses a sample story and placeholder illustrations.",
)

if not demo_mode:
    st.caption(
        "Live mode uses your configured AI APIs. "
        "API usage may incur charges."
    )

if st.button("✨ Generate Storybook", type="primary", use_container_width=True):
    if not prompt.strip():
        st.warning("Please enter a story idea first.")
    else:
        try:
            with st.spinner(
                "Creating your storybook... This may take a few minutes."
            ):
                result = run_story_pipeline(
                    user_prompt=prompt.strip(),
                    output_dir=OUTPUT_DIR,
                    max_revisions=1,
                    demo_mode=demo_mode,
                )

            st.session_state["storybook_result"] = result
            st.session_state["storybook_prompt"] = prompt.strip()

        except Exception as exc:
            st.error("Storybook generation failed.")
            st.exception(exc)

result = st.session_state.get("storybook_result")

if result:
    st.divider()
    st.header("🎉 Your storybook is ready!")

    st.success("The storybook PDF was created successfully.")

    pdf_path = Path(result["pdf_path"])

    if pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()

        st.download_button(
            label="⬇️ Download Storybook PDF",
            data=pdf_bytes,
            file_name="storybook.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

        st.caption(f"PDF size: {len(pdf_bytes) / 1024:.1f} KB")

    st.subheader("Your illustrations")

    reference_path = Path(result["character_reference"])

    if reference_path.exists():
        st.markdown("**Character reference**")
        st.image(str(reference_path), width=300)

    image_paths = result["image_paths"]

    if image_paths:
        columns = st.columns(2)

        for index, image_path in enumerate(image_paths):
            path = Path(image_path)

            with columns[index % 2]:
                st.markdown(f"**Page {index + 1}**")

                if path.exists():
                    st.image(str(path), use_container_width=True)
                else:
                    st.warning(f"Image not found: {path}")

    st.caption(
        "Demo mode was used."
        if result["demo_mode"]
        else "Generated using live AI APIs."
    )