"""
seed.py — Populate the database with test customer accounts.

Run once after the database tables have been created:

    python seed.py

Safe to run multiple times — existing records are not duplicated.
"""

import os
import sys

# Ensure BACKEND directory is on the path when run from the project root.
sys.path.insert(0, os.path.dirname(__file__))

from app import app
from auth import hash_password
from models import Customer, db

SEED_CUSTOMERS = [
    {
        "username": "john_doe",
        "password": "password123",
        "full_name": "John Doe",
        "balance": 1000.00,
    },
    {
        "username": "jane_smith",
        "password": "securepass",
        "full_name": "Jane Smith",
        "balance": 2500.00,
    },
]


def seed() -> None:
    with app.app_context():
        db.create_all()
        added = 0
        for data in SEED_CUSTOMERS:
            exists = Customer.query.filter_by(username=data["username"]).first()
            if exists:
                print(f"  [skip]  Customer '{data['username']}' already exists.")
                continue
            customer = Customer(
                username=data["username"],
                password_hash=hash_password(data["password"]),
                full_name=data["full_name"],
                balance=data["balance"],
            )
            db.session.add(customer)
            added += 1
            print(f"  [add]   Customer '{data['username']}' created.")

        db.session.commit()
        print(f"\nSeeding complete. {added} customer(s) added.")


if __name__ == "__main__":
    seed()
