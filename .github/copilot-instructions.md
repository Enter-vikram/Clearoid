# Copilot / AI Agent Instructions — Clearoid

This file gives concise, actionable guidance for AI coding agents working in this repository.

1) Big-picture architecture
- FastAPI app serves both frontend and API from [main.py](main.py). The frontend is static and mounted with `StaticFiles(directory="frontend", html=True)` so API and UI share the same port.
- Data layer: SQLAlchemy + SQLite at [database/database.py](database/database.py). The DB file is `titles.db` in the project root by default.
- Domain model: a single `Title` model in [models/title.py](models/title.py) storing raw and normalized titles, embeddings, duplicate flag, and timestamps.
- Services layer: business logic lives under `services/` (see `services/title_service.py` and `services/ml_service.py`). Routes call service functions; avoid duplicating logic in routes.
- Background jobs: RQ + Redis used for background workers (`worker.py`, `jobs.py`). Redis expected at localhost:6379 unless otherwise configured.

2) Primary code flows and examples
- Submit single title: POST `/submit` handled in [routes/title_routes.py](routes/title_routes.py) → calls `save_title(db, item)` in `services/title_service.py`.
- Bulk Excel upload: POST `/excel/upload-excel` (or `/bulk-upload` in title routes) expects a column named `title` and calls `process_bulk_titles(db, df)`.
- Duplicate detection: `get_embedding()` in [services/ml_service.py](services/ml_service.py) returns sentence-transformer embeddings. `services/title_service.py` uses `cosine_similarity` and thresholds (0.85 default) for duplicate detection.

3) Critical implementation details and gotchas
- Embedding storage: embeddings are stored either as a binary blob (`vec.tobytes()`) or sometimes as JSON strings. Code reads both forms using `np.frombuffer(...)` or `json.loads(...)`. When changing storage format, update all readers in `services/` and `routes/`.
- ML model load: `SentenceTransformer("all-MiniLM-L6-v2")` is loaded at import time in `services/ml_service.py`. This is heavy—avoid reloading in hot paths.
- DB session: use the `get_db` dependency from [database/database.py](database/database.py) in routes to obtain sessions; routes rely on the session lifecycle from that generator.
- Frontend routing: `app.mount("/", StaticFiles(...), name="frontend")` is last and catches unmatched routes. Register API routers before mounting if reordering.

4) Development and run commands
- Install dependencies (example):

```bash
python -m pip install fastapi uvicorn sqlalchemy pandas sentence-transformers scikit-learn rq redis python-dotenv
```

- Run development server:

```bash
uvicorn main:app --reload
```

- Run Redis (local) if needed:

```bash
docker run -p 6379:6379 redis
```

- Start RQ worker (listens to `default` queue):

```bash
python worker.py
```

Notes: `services/ml_service.py` will download the transformer model on first run; ensure network access and enough disk space.

5) Patterns & conventions unique to this repo
- Service-first: route handlers are thin; implement logic in `services/*` and call from `routes/*`.
- Data normalization: text cleaning is centralized in `utils/text_cleaner.py` — use it before encoding or comparing titles.
- Thresholds: duplicate thresholds are tuned in the service functions (0.85 used for bulk and 0.80–0.85 in other checks). Keep thresholds consistent unless intentionally changing behavior.
- Pydantic: models under `schemas/` use `model_config = {"from_attributes": True}` — return DB model instances directly when the route response_model expects them.

6) Integration points to be careful editing
- `services/ml_service.py` (model loading + encoding) — heavy, global side effects.
- `services/title_service.py` (bulk engine + duplicate logic) — central to correctness; reference when changing dedup rules.
- `routes/*` — rely on `get_db()`; ensure `db.commit()` and `db.refresh()` are used where expected.

7) When making changes, run these quick checks
- Start Redis + run `python worker.py` to ensure background queue compatibility.
- Run `uvicorn main:app --reload` and exercise `/submit` and `/excel/upload-excel` endpoints using `curl` or Postman.
- After DB schema changes, inspect `titles.db` (SQLite) or run a quick script that imports `models` and calls `Base.metadata.create_all(bind=engine)` as done in [main.py](main.py).

8) Where to look for examples
- API wiring: [main.py](main.py) and [routes/title_routes.py](routes/title_routes.py)
- Business logic: [services/title_service.py](services/title_service.py) and [services/ml_service.py](services/ml_service.py)
- DB model & session: [models/title.py](models/title.py) and [database/database.py](database/database.py)

If anything is unclear or you want more detail (run scripts, CI, or test guidance), tell me which area to expand. 
