import streamlit as st

_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Cinzel:wght@400;600;700&display=swap" rel="stylesheet">
<style>

/* Parchment background */
.stApp {
    background-color: #F2E0B6;
    background-image: radial-gradient(ellipse at top left, #E8D09A 0%, transparent 55%),
                      radial-gradient(ellipse at bottom right, #D4B87A 0%, transparent 55%);
}

/* Body & prose text — exclude icon elements */
body, p, li, td, th, blockquote,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    font-family: 'IM Fell English', Georgia, serif !important;
    color: #2C1810 !important;
}

/* Labels & captions (not icons) */
label, [data-testid="stCaptionContainer"] {
    font-family: 'IM Fell English', Georgia, serif !important;
    color: #5C3317 !important;
    font-style: italic !important;
}

/* Headings */
h1, h2, h3, h4, h5,
[data-testid="stHeading"] * {
    font-family: 'Cinzel', serif !important;
    color: #3D1F0D !important;
    letter-spacing: 0.06em;
    text-shadow: 1px 1px 2px rgba(100,60,20,0.15);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #E4CC8E !important;
    border-right: 2px solid #7A5C1E !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span:not(.material-symbols-outlined) {
    font-family: 'IM Fell English', Georgia, serif !important;
    color: #2C1810 !important;
}

/* Metric boxes */
[data-testid="metric-container"] {
    background-color: #EDD9A0 !important;
    border: 1px solid #7A5C1E !important;
    border-radius: 3px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Cinzel', serif !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em !important;
    color: #5C3317 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Cinzel', serif !important;
    color: #2C1810 !important;
}

/* Buttons */
.stButton > button {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.1em !important;
    border: 1px solid #7A5C1E !important;
    border-radius: 3px !important;
}
.stButton > button[kind="primary"] {
    background-color: #5C3317 !important;
    color: #F2E0B6 !important;
}
.stButton > button:not([kind="primary"]) {
    background-color: #E4CC8E !important;
    color: #3D1F0D !important;
}

/* Text input */
.stTextInput input, .stTextArea textarea {
    background-color: #FDF5E0 !important;
    border: 1px solid #7A5C1E !important;
    border-radius: 3px !important;
    font-family: 'IM Fell English', Georgia, serif !important;
    color: #2C1810 !important;
    font-size: 1rem !important;
}

/* Bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #7A5C1E !important;
    border-radius: 3px !important;
    background-color: rgba(242,224,182,0.5) !important;
}

/* Expander */
[data-testid="stExpander"] {
    border: 1px solid #7A5C1E !important;
    background-color: #FDF5E0 !important;
    border-radius: 3px !important;
}
[data-testid="stExpander"] summary p {
    font-family: 'Cinzel', serif !important;
    color: #3D1F0D !important;
    letter-spacing: 0.05em;
}

/* Search result chunk text */
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    font-family: 'IM Fell English', Georgia, serif !important;
    font-size: 1.05rem !important;
    line-height: 1.75 !important;
    color: #2C1810 !important;
}

/* Divider */
hr {
    border-color: #7A5C1E !important;
    opacity: 0.5;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #7A5C1E !important;
}
.stTabs [data-baseweb="tab"] p {
    font-family: 'Cinzel', serif !important;
    color: #5C3317 !important;
}
.stTabs [aria-selected="true"] p {
    color: #2C1810 !important;
}
.stTabs [aria-selected="true"] {
    border-bottom: 3px solid #5C3317 !important;
}

/* Alert / info boxes */
[data-testid="stAlert"] p {
    background-color: transparent !important;
    color: #2C1810 !important;
}
[data-testid="stAlert"] {
    background-color: #EDD9A0 !important;
    border: 1px solid #7A5C1E !important;
    border-radius: 3px !important;
}

/* Ornament helper */
.ornament {
    text-align: center;
    font-size: 1.4rem;
    color: #7A5C1E;
    letter-spacing: 0.5em;
    margin: 0.5rem 0;
}

/* Query highlight */
mark.q {
    background-color: #D4B87A !important;
    color: #2C1810 !important;
    padding: 0 0.15em;
    border-radius: 2px;
    font-weight: 600;
}

/* Summary card (Search page — key passages) */
.summary-card {
    background-color: #FDF5E0;
    border: 1px solid #7A5C1E;
    border-left: 4px solid #5C3317;
    border-radius: 3px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
}
.summary-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 0.5rem;
    gap: 1rem;
}
.summary-book {
    font-family: 'Cinzel', serif;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: #3D1F0D;
    font-size: 0.95rem;
}
.summary-sim {
    font-family: 'Cinzel', serif;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    color: #7A5C1E;
    white-space: nowrap;
}
.summary-text {
    font-family: 'IM Fell English', Georgia, serif;
    font-style: italic;
    font-size: 1.05rem;
    line-height: 1.7;
    color: #2C1810;
}

</style>
"""


def inject_theme():
    st.html(_CSS)
