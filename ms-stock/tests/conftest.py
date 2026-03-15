"""conftest.py for stock/tests — sets DATABASE_URL before any test module imports.

Uses a named temporary SQLite file so that Flask-SQLAlchemy's internal engine
(used by db.create_all) and the raw SQLAlchemy engine (SessionLocal in routes)
both connect to the same physical database. sqlite:///:memory: creates a separate
DB per engine instance and is not suitable for this dual-engine setup.

ERROR_RATE=0 eliminates random simulated errors during CRUD tests.
"""

import os
import tempfile

import pytest

# Create a temp SQLite file for the test session. setdefault means an externally-set
# DATABASE_URL (e.g. real PostgreSQL in CI) takes precedence.
_db_fd, _db_path = tempfile.mkstemp(suffix="_stock_test.db")
os.close(_db_fd)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")
# Disable the OTEL SDK during unit tests — no collector is running.
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("ERROR_RATE", "0")


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    """Remove the SQLite test file after the entire test session."""
    yield
    try:
        os.unlink(_db_path)
    except OSError:
        pass
