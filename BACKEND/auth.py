"""
auth.py — Password hashing and verification helpers.

All cryptographic work is delegated to Werkzeug's battle-tested
implementation (PBKDF2-HMAC-SHA256 with a random salt).
"""

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(raw_password: str) -> str:
    """
    Return a secure salted hash of *raw_password*.

    Use this only when creating or updating a customer's password
    (e.g. in the seed script).  Never store the raw password.
    """
    return generate_password_hash(raw_password)


def verify_password(stored_hash: str, submitted_password: str) -> bool:
    """
    Return True if *submitted_password* matches *stored_hash*, else False.

    Always returns a boolean — callers must never inspect the hash
    directly to avoid timing-attack vulnerabilities.
    """
    return check_password_hash(stored_hash, submitted_password)
