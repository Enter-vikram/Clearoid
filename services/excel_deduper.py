# services/excel_deduper.py

import pandas as pd
import re
from typing import Dict, List

from utils.text_cleaner import clean_text
from services.ml_service import hybrid_similarity
from services.embedding_service import embed_texts


# -----------------------------------
# Helpers
# -----------------------------------
def _remove_numbers(text: str) -> str:
    """
    Removes standalone numbers from text.
    Example:
      'sample title number 123' -> 'sample title number'
    """
    return re.sub(r"\b\d+\b", "", text).strip()


def _detect_title_column(df: pd.DataFrame, preferred: str = "title") -> str:
    """
    Detects which column should be treated as the title column.

    Priority:
    1. Exact match to preferred name (case-insensitive)
    2. Common title-like column names
    3. First text/object column
    """
    cols_lower = {c.lower(): c for c in df.columns}

    if preferred.lower() in cols_lower:
        return cols_lower[preferred.lower()]

    candidates = [
        "project title",
        "project_name",
        "topic",
        "idea",
        "name",
        "heading",
        "subject",
    ]

    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]

    for col in df.columns:
        if df[col].dtype == object:
            return col

    raise ValueError("No suitable text column found for deduplication")


# -----------------------------------
# Main dedupe function
# -----------------------------------
def dedupe_excel(
    df: pd.DataFrame,
    column: str = "title",
    ignore_numbers: bool = True,
    threshold: float = 0.85,
):
    """
    Semantic + deterministic Excel deduper.

    Returns:
    - unique_df: DataFrame with only unique rows
    - clusters: Dict[str, List[dict]]
    """

    if df.empty:
        raise ValueError("Uploaded Excel file is empty")

    df = df.copy()

    # -----------------------------------
    # Step 0: detect title column
    # -----------------------------------
    title_column = (
        column if column in df.columns
        else _detect_title_column(df, column)
    )

    df[title_column] = df[title_column].astype(str)

    # -----------------------------------
    # Step 1: normalize text
    # -----------------------------------
    df["_normalized"] = df[title_column].apply(clean_text)

    if ignore_numbers:
        df["_normalized"] = df["_normalized"].apply(_remove_numbers)

    df["_normalized"] = (
        df["_normalized"]
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )

    # -----------------------------------
    # Step 2: precompute embeddings ONCE
    # -----------------------------------
    texts = df["_normalized"].tolist()
    embeddings = embed_texts(texts)

    # -----------------------------------
    # Step 3: semantic clustering
    # -----------------------------------
    clusters: Dict[str, List[dict]] = {}
    cluster_embeddings: Dict[str, int] = {}  # primary -> index in df
    unique_indices: List[int] = []

    for idx, row in df.iterrows():
        current_text = row["_normalized"]

        if not current_text:
            continue

        current_emb = embeddings[idx]

        matched_key = None
        matched_score = 0.0

        for primary, primary_idx in cluster_embeddings.items():
            score = hybrid_similarity(current_text, primary)

            if score >= threshold:
                matched_key = primary
                matched_score = score
                break

        if matched_key is None:
            # New cluster
            clusters[current_text] = [{
                "title": row[title_column],
                "score": 1.0
            }]
            cluster_embeddings[current_text] = idx
            unique_indices.append(idx)
        else:
            clusters[matched_key].append({
                "title": row[title_column],
                "score": round(matched_score, 3)
            })

    # -----------------------------------
    # Step 4: build unique dataframe
    # -----------------------------------
    unique_df = df.loc[unique_indices].drop(columns=["_normalized"])

    return unique_df, clusters
