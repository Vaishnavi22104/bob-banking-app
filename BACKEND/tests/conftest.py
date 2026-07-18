"""
conftest.py — Shared pytest fixtures for the Banking application test suite.

Strategy
--------
- The Flask app is configured once per session with TESTING=True and an
  in-memory SQLite database so the real banking.db is never touched.
- Tables are created once at session start and dropped at session end.
- Each test that mutates data receives a clean slate via the `clean_db`
  fixture which deletes all rows from every table before the test runs.
"""

import os
import sys
import pytest

# Make BACKEND importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import app BEFORE reconfiguring so the module-level db.create_all() in
# app.py fires against the default URI; we immediately override it below.
import app as app_module
from auth import hash_password
from models import Customer, Transaction, db as _db


@pytest.fixture(scope="session")
def app():
    """
    Session-scoped Flask app wired to an in-memory SQLite database.
    Tables are created once and dropped after the whole test session.
    """
    app_module.app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret-key",
        }
    )
    with app_module.app.app_context():
        _db.create_all()
        yield app_module.app
        _db.drop_all()


@pytest.fixture()
def clean_db(app):
    """
    Function-scoped fixture.  Deletes all rows from every table before
    each test so tests never see each other's data.
    Yields the db object so tests can add rows directly if needed.
    """
    with app.app_context():
        Transaction.query.delete()
        Customer.query.delete()
        _db.session.commit()
        yield _db


@pytest.fixture()
def client(app):
    """Flask test client — sends requests without a real network connection."""
    return app.test_client()


@pytest.fixture()
def seeded_customer(clean_db, app):
    """
    Insert one known test customer (balance £500.00) and return it.
    Depends on clean_db so the table is empty before insert.
    """
    with app.app_context():
        customer = Customer(
            username="testuser",
            password_hash=hash_password("correctpassword"),
            full_name="Test User",
            balance=500.00,
        )
        clean_db.session.add(customer)
        clean_db.session.commit()
        # Re-query so the returned object is bound to the current session.
        return Customer.query.filter_by(username="testuser").first()
