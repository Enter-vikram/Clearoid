import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session

from backend.services.title_service import process_bulk_titles


def process_excel(file_bytes: bytes, db: Session):
    df = pd.read_excel(BytesIO(file_bytes))

    if "title" not in df.columns:
        raise ValueError("Excel must contain a column named 'title'")

    titles = (
        df["title"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return process_bulk_titles(titles, db)
