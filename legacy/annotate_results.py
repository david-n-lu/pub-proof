"""
annotate_results.py

Provides UI built with Streamlit to annotate product mentions in manufacturer sentences

To run:
python -m streamlit run annotate_results.py

Annotates product mentions of a sentence as Yes, Ok, or No
"""

import html
import re
import json

import pandas as pd
import streamlit as st

from legacy.export_sku_results import shorten_product_name


# INPUT
# - use original results .csv if no annotations made yet
# - use annotated results .csv if annotations already made
# CSV_PATH = "tests/data/matcher_results_without_sku_trademark_1000.csv"

from pathlib import Path


# CSV_PATH = "tests/data/matcher_results_without_sku_trademark_1000_annotated.csv"
# CSV_PATH = "data/europe_pmc/matcher_results_with_trademark_annotated.csv"
CSV_PATH = "data/europe_pmc/ollama_results_annotated.csv"
file_path = Path(CSV_PATH)

if not file_path.is_file():
    # CSV_PATH = "tests/data/matcher_results_without_sku_trademark_1000.csv"
    # CSV_PATH = "data/europe_pmc/matcher_results_with_trademark.csv"
    CSV_PATH = "data/europe_pmc/ollama_results.csv"

# OUTPUT
# SAVE_PATH = "tests/data/matcher_results_without_sku_trademark_1000_annotated.csv"
# SAVE_PATH = "data/europe_pmc/matcher_results_with_trademark_annotated.csv"
SAVE_PATH = "data/europe_pmc/ollama_results_annotated.csv"


# -------------------------
# Load
# -------------------------
def load_csv(path):
    df = pd.read_csv(path, encoding='utf-8-sig')

    if "validation" not in df.columns:
        df["validation"] = None

    return df



def save_progress():
    st.session_state.df.to_csv(SAVE_PATH, index=False, encoding="utf-8-sig")


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
            gap: 0.50rem;
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

df = st.session_state.df

if "idx" not in st.session_state:
    unvalidated = df[df["validation"].isna()]
    st.session_state.idx = (
        unvalidated.index[0] if not unvalidated.empty else 0
    )

if "save_counter" not in st.session_state:
    st.session_state.save_counter = 0


# -------------------------
# Get valid rows (unreviewed or all if navigating)
# -------------------------
rows = df.index.tolist()

idx = st.session_state.idx
idx = max(0, min(idx, len(df) - 1))

row = df.loc[idx]



# -------------------------
# Highlight using tokens of phrase
# -------------------------
def highlight_tokens(sentence, tokens):
    """
    Highlight given indexes of tokens
    """

    # print(tokens)
    # print(sentence)

    sentence = html.escape(str(sentence))

    sentence_norm = sentence.lower()

    DASH_RE = re.compile(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212\uFE58\uFE63\uFF0D]")

    sentence_norm = DASH_RE.sub("-", sentence_norm)

    idx = 0

    for token in tokens:

        old_idx = idx
        idx = sentence_norm.find(token, idx) if idx != -1 else sentence_norm.find(token)
        
        if idx == -1:
            idx = sentence_norm.find(token.replace(" ", "-"))

        if idx == -1:
            idx = old_idx
            continue

        start = idx
        end = start + len(token)

        sentence_norm = sentence_norm[:start] + "<mark>" + sentence_norm[start:end] + "</mark>" + sentence_norm[end:]
        sentence = sentence[:start] + "<mark>" + sentence[start:end] + "</mark>" + sentence[end:]

    # print(sentence)

    return sentence


def highlight_phrase(sentence, phrase):
    phrase = html.escape(str(phrase))
    phrase_norm = phrase.lower()

    tokens = phrase_norm.split(" ")
    tokens = list(dict.fromkeys(tokens))

    return highlight_tokens(sentence, tokens)


# -------------------------
# Title + progress
# -------------------------
# st.title("Publication Match Reviewer")
st.markdown("## Publication Match Reviewer")

done = df["validation"].notna().sum()
st.progress(done / len(df))

col1, col2 = st.columns([1, 5])

with col1:
    st.write(f"#### Row {idx + 1} / {len(df)}")


with col2:
    validation = df.loc[idx, "validation"] or "UNLABELED"
    status = {
        "YES": "🟩 YES",
        "OK": "🟨 OK",
        "NO": "🟥 NO",
        "SKIP": "⬜ SKIP",
    }.get(validation, "⬛ UNLABELED")
    
    st.write(f"#### Validation: {status}")


# -------------------------
# Product + match info
# -------------------------
skus = []
products = []
scores = []
score = -1

unique_products_string = ""
all_products_string = ""

if pd.notna(row.get("sku")) and pd.notna(row.get("product_name")) and pd.notna(row.get("score")):
    try:
        skus = json.loads(row["sku"])
        products = json.loads(row["product_name"])
        scores = json.loads(row["score"])
        
        if len(scores) > 0:
            # score = scores[0]
            score = " | ".join([str(s) for s in list(dict.fromkeys(scores))])
        else:
            score = 0
        
        all_products = []
        unique_products = []

        for i in range(len(skus)):
            sku = skus[i]
            product = products[i]

            all_products.append(f"{sku.upper()}: {product}")

            short = shorten_product_name(product)
            if short not in unique_products:
                unique_products.append(f"{short}")

        all_products_string = "</br>".join(all_products)
        unique_products = [f"<mark>{p}</mark>" for p in unique_products]
        unique_products_string = "</br>".join(unique_products)

    except:
        unique_products_string = "json.loads() failed"
        all_products_strings = "json.loads() failed"


col1, col2 = st.columns(2)

with col1:
    st.write("#### Product Info")
    st.write(f"**Manufacturer:** {row['manufacturer']}")
    st.write(f"**URL:** {row['url']}")


    st.write(f"**Unique Products: {len(unique_products)}**")
    # st.markdown( f"**Unique Products:** {unique_products_string}", unsafe_allow_html=True, )
    st.markdown(
        f"""
        <div style="
            width: 100%;
            height: 4.25em;
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5em;
            margin-bottom: 0.5em;
            box-sizing: border-box;
            white-space: nowrap;
        ">
            {unique_products_string}
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.write("#### Match Info")
    st.write(f"**Phrase:** {row['phrase']}")
    st.markdown( f"**Score:** <mark>{score}</mark>", unsafe_allow_html=True, )
    # st.write(f"**Score:** {row['score']}")

    st.write(f"**All Products: {len(products)}**")
    st.markdown(
        f"""
        <div style="
            width: 100%;
            height: 4.25em;
            overflow: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 0.5em;
            margin-bottom: 0.5em;
            box-sizing: border-box;
            white-space: nowrap;
        ">
            {all_products_string}
        </div>
        """,
        unsafe_allow_html=True,
    )


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

if token_indexes:
    highlighted = highlight_tokens(row["sentence"], token_indexes)
else:
    input_separator = "|"
    highlighted = highlight_phrase(row["sentence"], row["phrase"].replace(input_separator, " "))
# print(token_indexes)
# print(highlighted)

st.markdown(
    f"""
    <div style="
        height: 4.25em;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-bottom: 1em;
        padding: 6px;
    ">
        {highlighted}
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Navigation helpers
# -------------------------

SAVE_EVERY = 1

# saves
def set_label(label):
    idx = st.session_state.idx
    df.loc[idx, "validation"] = label

    st.session_state.save_counter += 1
    if st.session_state.save_counter >= SAVE_EVERY:
        save_progress()
        st.session_state.save_counter = 0

# doesn't save
def go(delta):
    st.session_state.idx = max(0, min(len(df) - 1, st.session_state.idx + delta))
    st.rerun()

# doesn't save
def go_to(idx):
    st.session_state.idx = max(0, min(len(df) - 1, idx - 1))
    st.rerun()

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
        go(-1)

with nav3:
    if st.button("Next ➡️", use_container_width=True):
        go(1)


col1, col2, col3, col4, col5 = st.columns([2, 0.3, 0.7, 1, 2])

with col2:
    st.markdown(
        """
        <div style="
            height: 2.25rem;
            display: flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
        ">
            Go to line:
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    target_idx = st.number_input(
        "Go to line",
        min_value=1,
        max_value=len(df),
        value=st.session_state.idx + 1,
        step=1,
        label_visibility="collapsed",
    )

# with col2:
#     st.write("")  # spacing hack
#     st.write(f"Current: {st.session_state.idx + 1}")

with col4:
    if st.button("Go ➜", use_container_width=True):
        go_to(int(target_idx))