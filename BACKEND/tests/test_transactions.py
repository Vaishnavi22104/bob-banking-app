"""
test_transactions.py — Unit tests for transactions.py (deposit and withdraw).

Each test uses the `seeded_customer` fixture (balance = £500.00) and a
clean database state provided by `seeded_customer` → `clean_db`.
"""

from transactions import deposit, withdraw


class TestDeposit:
    # --- Happy path -------------------------------------------------------

    def test_valid_deposit_increases_balance(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "100.00")
        assert success is True
        assert "100.00" in msg

    def test_deposit_success_message_contains_new_balance(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "50.00")
        assert success is True
        assert "550.00" in msg

    def test_deposit_whole_number_string(self, seeded_customer, app):
        with app.app_context():
            success, _ = deposit(seeded_customer.id, "200")
        assert success is True

    # --- Validation failures ----------------------------------------------

    def test_zero_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "0")
        assert success is False
        assert "greater than zero" in msg.lower()

    def test_negative_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "-50")
        assert success is False

    def test_non_numeric_string_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "abc")
        assert success is False
        assert "valid number" in msg.lower()

    def test_empty_string_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = deposit(seeded_customer.id, "")
        assert success is False

    def test_none_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, _ = deposit(seeded_customer.id, None)
        assert success is False


class TestWithdraw:
    # --- Happy path -------------------------------------------------------

    def test_valid_withdrawal_decreases_balance(self, seeded_customer, app):
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "100.00")
        assert success is True
        assert "100.00" in msg

    def test_withdraw_exact_balance_succeeds(self, seeded_customer, app):
        """Withdrawing the full balance should leave a balance of £0.00."""
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "500.00")
        assert success is True
        assert "0.00" in msg

    def test_withdraw_success_message_contains_new_balance(self, seeded_customer, app):
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "200.00")
        assert success is True
        assert "300.00" in msg

    # --- Validation failures ----------------------------------------------

    def test_exceeds_balance_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "600.00")
        assert success is False
        assert "insufficient" in msg.lower()

    def test_zero_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "0")
        assert success is False
        assert "greater than zero" in msg.lower()

    def test_negative_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, _ = withdraw(seeded_customer.id, "-10")
        assert success is False

    def test_non_numeric_string_rejected(self, seeded_customer, app):
        with app.app_context():
            success, msg = withdraw(seeded_customer.id, "hello")
        assert success is False
        assert "valid number" in msg.lower()

    def test_empty_string_rejected(self, seeded_customer, app):
        with app.app_context():
            success, _ = withdraw(seeded_customer.id, "")
        assert success is False

    def test_none_amount_rejected(self, seeded_customer, app):
        with app.app_context():
            success, _ = withdraw(seeded_customer.id, None)
        assert success is False
