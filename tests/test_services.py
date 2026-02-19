import numpy as np
import pytest
from sqlalchemy import delete

from backend.schemas.title_schema import TitleCreate
from backend.services.title_service import check_duplicate, count_duplicates, save_title
from database.connection import SessionLocal
from database.models import Title


@pytest.fixture(autouse=True)
def cleanup_test_rows():
    db = SessionLocal()
    try:
        yield
    finally:
        db.execute(delete(Title).where(Title.title.like("TEST_CASE_%")))
        db.commit()
        db.close()


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def fake_embedding(monkeypatch):
    def _embed(text: str):
        seed = abs(hash(text)) % (2 ** 32)
        rng = np.random.default_rng(seed)
        return rng.random(8, dtype=np.float32).tolist()

    monkeypatch.setattr("backend.services.title_service.get_embedding", _embed)


def test_save_title_duplicate_flag(db_session, fake_embedding):
    first = save_title(db_session, TitleCreate(title="TEST_CASE_Project One"))
    second = save_title(db_session, TitleCreate(title="TEST_CASE_Project One"))

    assert first.is_duplicate == 0
    assert second.is_duplicate == 1
    assert second.normalized_title == first.normalized_title


def test_check_duplicate_and_count(db_session, fake_embedding):
    save_title(db_session, TitleCreate(title="TEST_CASE_Project Two"))
    save_title(db_session, TitleCreate(title="TEST_CASE_Project Two"))

    result = check_duplicate(db_session, TitleCreate(title="TEST_CASE_Project Two"))
    assert result["duplicate"] is True
    assert result["match_id"] is not None
    assert result["score"] >= 0

    assert count_duplicates(db_session) >= 1
