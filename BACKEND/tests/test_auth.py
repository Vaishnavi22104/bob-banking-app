"""
test_auth.py — Unit tests for auth.py (password hashing and verification).

These tests exercise the auth helpers in complete isolation — no Flask
app context, no database, no HTTP requests.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import hash_password, verify_password


class TestHashPassword:
    def test_returns_a_string(self):
        result = hash_password("mysecretpassword")
        assert isinstance(result, str)

    def test_hash_is_not_the_raw_password(self):
        raw = "mysecretpassword"
        assert hash_password(raw) != raw

    def test_two_hashes_of_same_password_differ(self):
        """Werkzeug uses a random salt — two calls must not produce the same hash."""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_hash_is_non_empty(self):
        assert len(hash_password("x")) > 0


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        raw = "correctpassword"
        stored = hash_password(raw)
        assert verify_password(stored, raw) is True

    def test_wrong_password_returns_false(self):
        stored = hash_password("correctpassword")
        assert verify_password(stored, "wrongpassword") is False

    def test_empty_password_returns_false(self):
        stored = hash_password("correctpassword")
        assert verify_password(stored, "") is False

    def test_case_sensitive(self):
        stored = hash_password("Password123")
        assert verify_password(stored, "password123") is False

    def test_returns_bool_type(self):
        stored = hash_password("test")
        result = verify_password(stored, "test")
        assert isinstance(result, bool)
