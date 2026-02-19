import re
import os

IGNORE_NUMBERS = os.getenv("IGNORE_NUMBERS", "true").lower() == "true"

def clean_text(text: str) -> str:
    text = text.lower()

    if IGNORE_NUMBERS:
        text = re.sub(r"\d+", "", text)

    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()
