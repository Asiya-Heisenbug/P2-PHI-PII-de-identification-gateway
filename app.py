import streamlit as st

from src.detector import detect, mode
from src.security import MappingStore
from src.deidentifier import deidentify
from src.rehydrator import rehydrate
from src.llm import ask_llm


st.set_page_config(
    page_title="PHI SHIELD",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#18343b; --muted:#6c8184; --teal:#167d76; --teal-soft:#e5f4f1; --line:#dce8e5; --paper:#f7faf8; }
    .stApp { background:var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:#edf5f2; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top:2rem; }
    h1,h2,h3 { font-family:'Space Grotesk',sans-serif; color:var(--ink); }
    p,label,.stMarkdown,.stCaption { font-family:'DM Sans',sans-serif; }
    h1 { letter-spacing:0; font-size:2.35rem; margin-bottom:.25rem; }
    .brand-mark { display:flex; align-items:center; gap:.75rem; margin-bottom:2.5rem; }
    .brand-icon { width:42px; height:42px; display:grid; place-items:center; border-radius:12px; background:var(--teal); color:white; font-size:1.3rem; }
    .brand-name { font-family:'Space Grotesk'; font-weight:700; color:var(--ink); }
    .brand-sub { color:var(--muted); font-size:.78rem; }
    .eyebrow { color:var(--teal); font-size:.75rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.7rem; }
    .hero-copy { max-width:680px; color:var(--muted); font-size:1.03rem; line-height:1.65; }
    .privacy-card { border:1px solid #b9ddd6; border-radius:14px; background:var(--teal-soft); padding:1.25rem 1.35rem; min-height:145px; }
    .privacy-title { color:var(--teal); font-weight:700; margin-bottom:.45rem; }
    .privacy-copy { color:#3f6766; font-size:.88rem; line-height:1.5; }
    .section-label { font-family:'Space Grotesk'; color:var(--ink); font-size:1.1rem; font-weight:600; margin:2rem 0 .75rem; }
    .status-row { display:flex; gap:.6rem; align-items:center; padding:.65rem .2rem; color:#476265; font-size:.9rem; border-bottom:1px solid #d7e7e2; }
    .status-dot { width:8px; height:8px; border-radius:50%; background:#36a47f; }
    .side-note { color:var(--muted); font-size:.78rem; line-height:1.5; margin-top:2rem; }
    .result-label { color:var(--teal); font-size:.76rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.45rem; }
    .metric-card { border:1px solid var(--line); background:white; border-radius:12px; padding:.8rem 1rem; text-align:center; }
    .metric-value { color:var(--ink); font-family:'Space Grotesk'; font-size:1.35rem; font-weight:700; }
    .metric-name { color:var(--muted); font-size:.72rem; margin-top:.15rem; }
    div.stButton > button { border-radius:9px; border:0; background:var(--teal); color:white; font-family:'DM Sans'; font-weight:700; padding:.7rem 1.2rem; }
    div.stButton > button:hover { background:#106861; color:white; }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        """
        <div class="brand-mark">
            <div class="brand-icon">✚</div>
            <div><div class="brand-name">PHI SHIELD</div>
            <div class="brand-sub">Clinical privacy gateway</div></div>
        </div>
        <div class="eyebrow">System status</div>
        <div class="status-row"><span class="status-dot"></span> PHI detector online</div>
        <div class="status-row"><span class="status-dot"></span> Local masking active</div>
        <div class="status-row"><span class="status-dot"></span> Ollama connection ready</div>
        <div class="side-note">Patient identifiers stay inside this application. Only protected text is sent to the local model.</div>
        """,
        unsafe_allow_html=True
    )

header_left, header_right = st.columns([1.35, .65], gap="large")

with header_left:
    st.markdown('<div class="eyebrow">Private clinical workspace</div>', unsafe_allow_html=True)
    st.title("Clinical assistant, with a privacy boundary.")
    st.markdown(
        '<div class="hero-copy">Ask a clinical question in natural language. PHI SHIELD detects sensitive details, masks them before inference, and restores approved values only in the final response.</div>',
        unsafe_allow_html=True
    )

with header_right:
    st.markdown(
        """
        <div class="privacy-card">
            <div class="privacy-title">Protected by default</div>
            <div class="privacy-copy">Detection and rehydration happen locally. The model receives placeholders instead of patient identifiers.</div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown('<div class="section-label">New clinical request</div>', unsafe_allow_html=True)

user_text = st.text_area(
    "Clinical question or note",
    height=155,
    label_visibility="collapsed",
    placeholder=(
        "Example: Patient John Anderson has a blood sugar level of 180 mg/dL.\n"
        "What are common causes of high blood sugar?"
    )
)

action_left, action_right = st.columns([1, 3])
with action_left:
    ask = st.button("Analyze securely", type="primary", use_container_width=True)
with action_right:
    st.caption("Your text is scanned before it reaches the local clinical model.")

if ask:
    if not user_text.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Detecting sensitive information..."):
        spans = detect(user_text)

    store = MappingStore()
    masked_text, _ = deidentify(user_text, spans, store)
    detected_count = len(spans)

    st.markdown('<div class="section-label">Privacy review</div>', unsafe_allow_html=True)
    metric_one, metric_two, metric_three = st.columns(3)
    with metric_one:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{detected_count}</div><div class="metric-name">Protected items</div></div>', unsafe_allow_html=True)
    with metric_two:
        detector_mode = mode().replace("_", " ").title()
        st.markdown(f'<div class="metric-card"><div class="metric-value">{detector_mode}</div><div class="metric-name">Detector mode</div></div>', unsafe_allow_html=True)
    with metric_three:
        st.markdown('<div class="metric-card"><div class="metric-value">Local</div><div class="metric-name">Inference boundary</div></div>', unsafe_allow_html=True)

    if detected_count:
        st.success(f"{detected_count} sensitive item(s) detected and protected.")
    else:
        st.info("No sensitive information detected.")

    st.markdown('<div class="section-label">How the text was protected</div>', unsafe_allow_html=True)
    with st.expander("View detection labels, conversion, and stored mapping", expanded=True):
        if spans:
            conversion_rows = []
            for start, end, label in spans:
                original_value = user_text[start:end]
                conversion_rows.append({
                    "Detected text": original_value,
                    "Label used": label,
                    "Converted to": store.forward.get(original_value, "Not mapped"),
                    "Character span": f"{start}:{end}",
                })

            st.dataframe(
                conversion_rows,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("No sensitive spans were detected, so no replacements were stored.")

        st.markdown("**Original text**")
        st.code(user_text, language="text")

        st.markdown("**Converted text sent to the local model**")
        st.code(masked_text, language="text")

        if store.forward:
            st.markdown("**Local mapping store**")
            st.json(store.forward)

    with st.spinner("Asking local AI model..."):
        response = ask_llm(masked_text)

    restored_response, unknown = rehydrate(response, store)
    masked_col, response_col = st.columns(2, gap="large")
    with masked_col:
        st.markdown('<div class="result-label">Protected prompt</div>', unsafe_allow_html=True)
        st.code(masked_text, language="text")
    with response_col:
        st.markdown('<div class="result-label">Local model response</div>', unsafe_allow_html=True)
        st.code(response, language="text")
        st.markdown('<div class="result-label">Rehydrated response</div>', unsafe_allow_html=True)
        st.write(restored_response)

    if unknown:
        st.warning(f"Some placeholders could not be restored: {unknown}")

    with st.expander("🔎 Security Details"):
        st.write(f"**Detector mode:** `{mode()}`")
        st.write(f"**PHI entities detected:** `{detected_count}`")
        st.write("**External API:** `None`")
        st.write("**LLM:** `llama3.2:latest` via Ollama")
        st.write("**Original patient information is not sent to an external API.**")
