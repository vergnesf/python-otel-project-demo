"""conftest.py for order/tests — sets DATABASE_URL before any test module imports."""

import os

# Use SQLite in-memory so Flask smoke tests run without a PostgreSQL instance.
# If DATABASE_URL is already set in the environment (e.g. overridden externally), that value is used instead.
# Note: SQLite may not catch PostgreSQL-specific constraints (FK cascades, custom column types).
# These tests verify the app starts and the /health endpoint responds — not schema migration fidelity.
# Scope: this conftest.py applies to all files under order/tests/. Future test files in this
# directory will inherit DATABASE_URL=sqlite:///:memory: unless they reassign os.environ["DATABASE_URL"] directly.
# Timing: pytest loads conftest.py before importing test modules in this directory, so DATABASE_URL
# is set before any module-level code in test files here runs — including module-level model imports.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
