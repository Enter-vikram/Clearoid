# =============================================================================
# DEAD CODE — DO NOT IMPORT
#
# This directory is a pre-refactor duplicate of the active code in:
#   backend/routes/      (API endpoints)
#   backend/services/    (business logic)
#   backend/schemas/     (Pydantic models)
#
# All files here import from non-existent modules (database.database,
# models.*, services.*, schemas.*) and will fail immediately if imported.
# They are retained only for reference and will be deleted before the next
# major release.
#
# Nothing in main.py, the active routes, or the test suite imports from
# backend.app.*  — verified 2024.
# =============================================================================
raise ImportError(
    "backend.app is dead code and must not be imported. "
    "Use backend.routes, backend.services, and backend.schemas instead."
)
