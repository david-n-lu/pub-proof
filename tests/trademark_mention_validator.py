import html
import re
import json

import pandas as pd
import streamlit as st


from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from matching.normalization import normalize_for_matching
from export_sku_results import shorten_product_name


# from tests.trademark_mention import run_pipeline


manufacturer = "GeneCopoeia"
sentence_corpus_path = "tests/data/genecopoeia_sentences_1000.jsonl"
product_map_path = "data/raw_products"
output_csv_path = "tests/data/matcher_results_without_sku_trademark_1000.csv"

# run_pipeline(manufacturer=manufacturer,
#                 sentence_corpus_path=sentence_corpus_path,
#                 product_map_path=product_map_path,
#                 output_csv_path=output_csv_path)


CSV_PATH = "tests/data/matcher_results_without_sku_trademark_1000_annotated.csv"
SAVE_PATH = "tests/data/matcher_results_without_sku_trademark_1000_annotated.csv"


# -------------------------
# Load
# -------------------------
@st.cache_data
def load_csv(path):
    df = pd.read_csv(path, encoding='utf-8-sig')

    if "validated" not in df.columns:
        df["validated"] = None

    return df


def save_progress(df):
    df.to_csv(SAVE_PATH, index=False, encoding='utf-8-sig')


# -------------------------
# Highlight using token indexes
# -------------------------
def highlight_tokens(sentence, tokens):

    sentence_norm = sentence.lower()
    sentence = html.escape(str(sentence))

    idx = 0

    for token in tokens:

        old_idx = idx
        idx = sentence_norm.find(token, idx) if idx != -1 else sentence_norm.find(token)

        if idx == -1:
            idx = old_idx
            continue

        start = idx
        end = start + len(token)

        sentence_norm = sentence_norm[:start] + "<mark>" + sentence_norm[start:end] + "</mark>" + sentence_norm[end:]
        sentence = sentence[:start] + "<mark>" + sentence[start:end] + "</mark>" + sentence[end:]

    return sentence


def highlight_phrases(text, phrases):
    if pd.isna(text):
        return ""

    text = html.escape(str(text))

    # Longest first to avoid nested highlights
    phrases = sorted(
        [p.strip() for p in phrases if p.strip()],
        key=len,
        reverse=True,
    )

    for phrase in phrases:
        escaped_phrase = html.escape(phrase)

        text = re.sub(
            re.escape(escaped_phrase),
            f"<mark>{escaped_phrase}</mark>",
            text,
            flags=re.IGNORECASE,
        )

    return text

# -------------------------
# Get rid of padding so no scrollbar most of the time
# -------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 0rem !important;
        }

        header {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* reduce default element spacing */
        div[data-testid="stVerticalBlock"] {
            gap: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------
# Session state setup
# -------------------------


st.set_page_config(layout="wide")

if "df" not in st.session_state:
    st.session_state.df = load_csv(CSV_PATH)

if "idx" not in st.session_state:
    st.session_state.idx = 0

df = st.session_state.df


# -------------------------
# Get valid rows (unreviewed or all if navigating)
# -------------------------
rows = df.index.tolist()

idx = st.session_state.idx
idx = max(0, min(idx, len(df) - 1))

row = df.loc[idx]


# -------------------------
# Title + progress
# -------------------------
# st.title("Publication Match Reviewer")
st.markdown("## Publication Match Reviewer")

done = df["validated"].notna().sum()
st.progress(done / len(df))

st.write(f"#### Row {idx + 1} / {len(df)}")


# -------------------------
# Product + match info
# -------------------------
col1, col2 = st.columns(2)

with col1:
    st.write("#### Product Info")
    st.write(f"**Manufacturer:** {row['manufacturer']}")
    st.write(f"**SKU:** {row['sku']}")

    product_name = row['product_name']
    highlight_length = len(shorten_product_name(product_name))
    product_name = "<mark>" + product_name[:highlight_length] + "</mark>" + product_name[highlight_length:]

    st.markdown( f"**Product Name:** {product_name}", unsafe_allow_html=True, )

with col2:
    st.write("#### Match Info")
    st.write(f"**Phrase:** {row['phrase']}")
    st.markdown( f"**Score:** <mark>{row['score']}</mark>", unsafe_allow_html=True, )
    # st.write(f"**Score:** {row['score']}")
    st.write(f"**URL:** {row['url']}")


# -------------------------
# Token parsing (FIXED)
# -------------------------
token_indexes = []

if pd.notna(row.get("token_indexes")):
    try:
        # supports "[1,2,3]" style
        token_indexes = json.loads(row["token_indexes"])
    except:
        token_indexes = []

    # if dict -> values
    if isinstance(token_indexes, dict):
        token_indexes = list(token_indexes.values())


# -------------------------
# Sentence highlight
# -------------------------
st.write("#### Sentence")

highlighted = highlight_tokens(row["sentence"], token_indexes)

st.markdown(highlighted, unsafe_allow_html=True)


# -------------------------
# Navigation helpers
# -------------------------
def go(delta):
    st.session_state.idx = max(0, min(len(df) - 1, st.session_state.idx + delta))
    st.rerun()


def set_label(label):
    df.at[idx, "validated"] = label
    save_progress(df)
    st.session_state.df = df


# -------------------------
# Buttons: labels
# -------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("🟩 YES", use_container_width=True):
        set_label("YES")
        go(1)

with c2:
    if st.button("🟨 OK", use_container_width=True):
        set_label("OK")
        go(1)

with c3:
    if st.button("🟥 NO", use_container_width=True):
        set_label("NO")
        go(1)

with c4:
    if st.button("⬜ SKIP", use_container_width=True):
        set_label("SKIP")
        go(1)


# -------------------------
# Buttons: navigation
# -------------------------
nav1, nav2, nav3 = st.columns(3)

with nav1:
    if st.button("⬅️ Back", use_container_width=True):
        save_progress(df)
        go(-1)

with nav3:
    if st.button("Next ➡️", use_container_width=True):
        save_progress(df)
        go(1)