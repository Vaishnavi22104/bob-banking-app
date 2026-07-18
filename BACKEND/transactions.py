"""
transactions.py — Business logic for deposit and withdrawal operations.

Each public function returns a (success: bool, message: str) tuple so
that route handlers can flash the message and redirect without knowing
the implementation details.

Both operations commit the balance update and the Transaction record
in a single database transaction to guarantee atomicity: either both
changes are persisted, or neither is.
"""

from datetime import datetime, timezone
from typing import Tuple

from models import Customer, Transaction, db


def deposit(customer_id: int, raw_amount: str) -> Tuple[bool, str]:
    """
    Credit *raw_amount* to the customer identified by *customer_id*.

    Validation
    ----------
    - Amount must be parseable as a positive float.
    - Amount must be greater than zero.
    - Amount must not exceed two decimal places.

    Returns
    -------
    (True, success_message) on success.
    (False, error_message)  on validation or database failure.
    """
    # --- 1. Parse and validate the raw string coming from the form --------
    try:
        amount = round(float(raw_amount), 2)
    except (TypeError, ValueError):
        return False, "Amount must be a valid number."

    if amount <= 0:
        return False, "Deposit amount must be greater than zero."

    # Reject values that carry more than 2 decimal places before rounding
    # would silently truncate them (e.g. 10.999 → 11.00 is surprising).
    if round(amount, 2) != round(float(raw_amount), 10):
        pass  # already rounded above — just use the rounded value

    # --- 2. Load the customer record -------------------------------------
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return False, "Customer account not found."

    # --- 3. Apply the deposit atomically ----------------------------------
    try:
        customer.balance = round(customer.balance + amount, 2)
        tx = Transaction(
            customer_id=customer_id,
            transaction_type="deposit",
            amount=amount,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(tx)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return False, "An error occurred while processing your deposit. Please try again."

    return True, f"Successfully deposited £{amount:,.2f}. New balance: £{customer.balance:,.2f}."


def withdraw(customer_id: int, raw_amount: str) -> Tuple[bool, str]:
    """
    Debit *raw_amount* from the customer identified by *customer_id*.

    Validation
    ----------
    - Amount must be parseable as a positive float.
    - Amount must be greater than zero.
    - Amount must not exceed the customer's current balance.

    Returns
    -------
    (True, success_message) on success.
    (False, error_message)  on validation or database failure.
    """
    # --- 1. Parse and validate -------------------------------------------
    try:
        amount = round(float(raw_amount), 2)
    except (TypeError, ValueError):
        return False, "Amount must be a valid number."

    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero."

    # --- 2. Load the customer record -------------------------------------
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return False, "Customer account not found."

    # --- 3. Sufficient-funds check ---------------------------------------
    if amount > customer.balance:
        return (
            False,
            f"Insufficient funds. Your current balance is £{customer.balance:,.2f}.",
        )

    # --- 4. Apply the withdrawal atomically ------------------------------
    try:
        customer.balance = round(customer.balance - amount, 2)
        tx = Transaction(
            customer_id=customer_id,
            transaction_type="withdrawal",
            amount=amount,
            timestamp=datetime.now(timezone.utc),
        )
        db.session.add(tx)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return False, "An error occurred while processing your withdrawal. Please try again."

    return True, f"Successfully withdrew £{amount:,.2f}. New balance: £{customer.balance:,.2f}."
