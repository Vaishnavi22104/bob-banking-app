"""
models.py — SQLAlchemy data models for the Banking application.

Tables
------
Customer     – registered bank customer with credentials and balance.
Transaction  – immutable ledger entry for every deposit or withdrawal.
"""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    """Represents a registered bank customer."""

    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False, default="")
    balance = db.Column(db.Float, nullable=False, default=0.0)

    # One-to-many: a customer owns many transactions.
    transactions = db.relationship(
        "Transaction",
        backref="customer",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} username={self.username!r}>"


class Transaction(db.Model):
    """Immutable record of a single deposit or withdrawal."""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Either "deposit" or "withdrawal" — always stored as a positive amount.
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.transaction_type!r} "
            f"amount={self.amount} customer_id={self.customer_id}>"
        )
