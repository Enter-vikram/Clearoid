# services/excel_deduper.py

import pandas as pd
import re
from utils.text_cleaner import clean_text


def _remove_numbers(text: str) -> str:
    """
    Removes standalone numbers from text.
    Example:
      'sample title number 123' -> 'sample title number'
    """
    return re.sub(r"\b\d+\b", "", text).strip()


def dedupe_excel(
    df: pd.DataFrame,
    column: str = None,
    ignore_numbers: bool = True,
):
    """
    Deterministic Excel deduper.

    Parameters:
    - df: input DataFrame
    - column: column containing titles (auto-detects first column if None)
    - ignore_numbers:
        True  -> 'Title 1', 'Title 2' are duplicates
        False -> treated as unique

    Returns:
    - unique_df: DataFrame with only unique rows
    - clusters: dict[str, list[str]]
        {
          normalized_title: [original titles...]
        }
    """

    if column is None:
        column = df.columns[0]
    
    if column not in df.columns:
        raise ValueError(f"Excel must contain a '{column}' column")

    df = df.copy()
    df[column] = df[column].astype(str)

    # -------------------------------------------------
    # Step 1: normalize text (lowercase, punctuation)
    # -------------------------------------------------
    df["normalized"] = df[column].apply(clean_text)

    # -------------------------------------------------
    # Step 2: optionally strip numbers
    # -------------------------------------------------
    if ignore_numbers:
        df["normalized"] = df["normalized"].apply(_remove_numbers)

    # Final cleanup (collapse spaces after number removal)
    df["normalized"] = df["normalized"].str.replace(r"\s+", " ", regex=True).str.strip()

    # -------------------------------------------------
    # Step 3: build clusters (DO NOT DELETE INFO)
    # -------------------------------------------------
    clusters = (
        df.groupby("normalized")[column]
        .apply(list)
        .to_dict()
    )

    # -------------------------------------------------
    # Step 4: deterministic dedupe
    # Keep FIRST occurrence only (order-preserving)
    # -------------------------------------------------
    unique_df = df.drop_duplicates(subset="normalized", keep="first")

    return unique_df, clusters
